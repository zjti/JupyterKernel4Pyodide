import asyncio
import threading
import websockets
import json
import os

def run_coro(coro):
    #event loop should be running if exceuted from IPyKernel
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
    except:
        asyncio.run(coro)
        
    
    
s = """
import os
dst = '{}'
os.makedirs(os.path.dirname(dst), exist_ok=True)
with open(dst,'w') as f: 
    for line in {}:
        f.write(line)
"""

def copy_file_to_pyodide(src,dst):
    async def async_copy_file_to_pyodide(src,dst):
        with open(src,'r') as f:
            lines = f.readlines()

        code = s.format(dst,str(lines))

        async with websockets.connect('ws://localhost:8787/') as c:
            await c.send(json.dumps({'type':'code', 'code':code}))

        print(code)
    run_coro(async_copy_file_to_pyodide(src,src)) 

    
def copy_dir_to_pyodide(srcpath, dstpath=None):
    for cdir,subdirs,files in os.walk(srcpath):
        subdirs[:] = [d for d in subdirs if not d[0] == '.']

        srcfiles = [os.path.join(cdir,f) for f in files]
        if dstpath:
            dstfiles = [src.replace(srcpath,dstpath) for src in srcfiles]
        else:
            dstfiles = srcfiles
        [run_coro(copy_file_to_pyodide(src,dst)) for src,dst in zip(srcfiles,dstfiles)]
        
# import2pyodide()