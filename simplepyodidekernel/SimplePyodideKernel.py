from ipykernel.kernelbase import Kernel

import asyncio
import websockets
import json
import psutil

PORT = 8889

to_ws_queue = asyncio.Queue()
from_ws_queue = asyncio.Queue()
from_ws_to_compl_queue = asyncio.Queue()
connected= set()
connected_code_backdoor = set()

async def ws_handler(websocket): 
    
    connected.add(websocket) 
    #clear queue:
    for _ in range(from_ws_queue.qsize()):
            from_ws_queue.get_nowait()
            from_ws_queue.task_done()
            
   
    try:
        # Broadcast a message to all connected clients.
        while True: 
            msg = await to_ws_queue.get()
            print('to',msg)
            await websocket.send(json.dumps(msg))
            
            if msg['type'] == 'code': 
                while True:
                    resp= json.loads(await websocket.recv())
                    print('from',resp)
                    
                    if 'ignore_response' not in msg:
                        from_ws_queue.put_nowait(resp)
                     
                    if resp['type']=='cmd' and resp['data']=='break':
                        break
                    if resp['type']=='return':
                        break
            elif msg['type'] == 'compl_req':
                
                resp = json.loads( await websocket.recv()) 
                from_ws_to_compl_queue.put_nowait(resp)
                break
                
    except: 
        pass
    finally:
        # Unregister.
        from_ws_queue.put_nowait({'type':'return','data':'error in websockethandler'})
        connected.remove(websocket)

async def ws_handler_code_backdoor(websocket): 
    connected_code_backdoor.add(websocket)
   
    try:
        while True: 
            msg= json.loads(await websocket.recv())
            print(msg)
            msg['ignore_response'] = True
            to_ws_queue.put_nowait(msg)
    except: 
        pass
    finally:
        # Unregister.
        connected_code_backdoor.remove(websocket)


class SimplePyodideKernel(Kernel):
    implementation =''
    implementation_version = '0.0.1'
    language = 'python'
    language_info = {
        'name': 'python',
        'mimetype': "text/x-python",
        'file_extension': '.py',
    }
    banner = "Simple Pyodide Kernel"
    
    def __init__(self,**kwargs):
        Kernel.__init__(self, **kwargs)
        self.last_complete_req = None
        
    def do_shutdown(self,restart):
        if restart:
            to_ws_queue.put_nowait({'type':'cmd','data':'reload'})
        
    async def do_execute(self, code, silent, store_history=True, user_expressions=None,
                   allow_stdin=False):
        
        if code == 'exit':
            self.do_shutdown(restart=False)
            [p.kill() for p in psutil.process_iter() if 'SimplePyodideKerenel' in  p.cmdline()]
            [p.kill() for p in psutil.process_iter() if 'simple_pyodide_kernel' in  p.cmdline()]
        
        rv = {'status': 'ok',
                'execution_count': self.execution_count,
                'payload': [],
                'user_expressions': {},
               }
          
        if len(connected) == 0:
            stream_content = {'name': 'stdout', 'text':" NO WEB-CLIENT  \n" }
            self.send_response(self.iopub_socket, 'stream', stream_content)
            return rv 
        
        to_ws_queue.put_nowait({'type':'code','code':code})

         
        while True:
            resp = await from_ws_queue.get() 
            
            if resp['type']=='cmd' and resp['data']=='break':
                break
            if resp['type']=='return':
                if not silent:
                    stream_content = {'name': 'stdout', 'text': str( resp['data'])}
                    self.send_response(self.iopub_socket, 'stream', stream_content)
                break
            
            elif resp['type']=='stdout':
                if not silent:
                    stream_content = {'name': 'stdout', 'text': str(resp['data'])}
                    self.send_response(self.iopub_socket, 'stream', stream_content)
            elif resp['type']=='stderr':
                if not silent:
                    stream_content = {'name': 'stderr', 'text': str(resp['data'])}
                    self.send_response(self.iopub_socket, 'stream', stream_content)
                    
        
        return rv
    
    async def do_complete(self, code, cursor_pos):
        if self.last_complete_req == (code,cursor_pos):
            return self.last_complet_resp
        else:
            self.last_complete_req = (code,cursor_pos)
        
        code = code[:cursor_pos]
        default = {'matches': ['abc','abcde'], 'cursor_start': cursor_pos,
                   'cursor_end': cursor_pos, 'metadata': dict(),
                   'status': 'ok'}
        self.last_complet_resp = default
        
        if not code or code[-1] == ' ':
            return default
        
        print(code,cursor_pos)
        to_ws_queue.put_nowait({'type':'compl_req','code':code})
        
        resp = await from_ws_to_compl_queue.get() 
        print(resp['start'])
        
        #matches = [m[cursor_pos-resp['start']:] for m in resp['completions']]
        matches =  resp['completions']
        default = {'matches': matches , 'cursor_start': resp['start'],
                   'cursor_end': cursor_pos, 'metadata': dict(),
                   'status': 'ok'}
        
        self.last_complet_resp = default
        return default

        

if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    print(1234)
    loop.run_until_complete(websockets.serve(ws_handler, '127.0.0.1', PORT))
    loop.run_until_complete(websockets.serve(ws_handler_code_backdoor, '127.0.0.1', 8787))
    IPKernelApp.launch_instance(kernel_class=SimplePyodideKernel)
    
    
    
    
    