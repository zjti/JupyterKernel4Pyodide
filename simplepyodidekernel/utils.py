import asyncio
import threading
import websockets
import json
import os
from multiprocessing import Process

from simplepyodidekernel.SimplePyodideKernel import PORT_CODE_BACKDOOR

def send_code_to_pyodide(code):
    """ Send code via websockets to the Pyodide-Kernel and wait till the end of exceution.
        
        The PyodideKernel then redirects the given code to the pyodide instance.
        To manage the async websocket-connection from the jupyterkernel enviorment 
        (e.g. a Notebook) a multiprocess.Process is spawned wich will then run its own eventloop 
        for the websocket-communication.
    """
    
    def t():
        async def async_send_code(code):
            async with websockets.connect('ws://localhost:{}/'.format(PORT_CODE_BACKDOOR)) as c:
                await c.send(json.dumps({'type':'code', 'code':code}))

                while True:
                    print('pyodied respone:')
                    resp = await c.recv()
                    resp = json.loads(resp)
                    print(resp)
                    if resp['type']=='cmd' and resp['data']=='break':
                        break
                    if resp['type']=='return':
                        break 

        coro = async_send_code(code)
        loop=asyncio.new_event_loop()
        loop.run_until_complete( coro )

    
    p = Process(target=t)
    p.start()
    p.join()
    
        
writefile_template = """
import os
import shutil
dst = '{}'
os.makedirs(os.path.dirname(dst), exist_ok=True)
with open(dst,'w') as f: 
    for line in {}:
        f.write(line)
"""
        
def copy_file_to_pyodide(src,dst):
    """ copy a single file to the pyodide-inbrowser-filesystem"""
    with open(src,'r') as f:
        lines = f.readlines()

    code = writefile_template.format(dst,str(lines))
    send_code_to_pyodide(code)
    
    
rmold_code = """
import shutil
shutil.rmtree("{}")
"""
    
def copy_dir_to_pyodide(srcpath, dstpath=None):
    """ copy a directory to the pyodide-inbrowser-filesystem"""
    
    srcdirname = os.path.dirname(srcpath)
    if dstpath:
        dstdirname = os.path.dirname(dstpath)
    else:
        dstdirname = srcdirname

    
    for cdir,subdirs,files in os.walk(srcpath):
        subdirs[:] = [d for d in subdirs if not d[0] == '.']

        srcfiles = [os.path.join(cdir,f) for f in files]
        if dstpath:
            dstfiles = [src.replace(srcdirname,dstdirname) for src in srcfiles]
        else:
            dstfiles = srcfiles
        [copy_file_to_pyodide(src,dst) for src,dst in zip(srcfiles,dstfiles)]
        