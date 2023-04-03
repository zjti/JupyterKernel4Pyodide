function sleep(s) {
return new Promise((resolve) => setTimeout(resolve, s));
}

    
async function main() {
let term;
globalThis.pyodide = await loadPyodide({
  stdin: () => {
    let result = prompt();
    echo(result);
    return result;
  }
});
let namespace = pyodide.globals.get("dict")();
pyodide.runPython(`
import sys
from pyodide.ffi import to_js
from pyodide.console import PyodideConsole, repr_shorten, BANNER
import __main__

import traceback
from contextlib import redirect_stdout,redirect_stderr
import io
import json

from pyodide.code import eval_code
from js import WebSocket, console, sleep, location

PORT = 8889

socket = WebSocket.new("ws://127.0.0.1:{}/".format(PORT)) 

def socketsend(dict_data):
    socket.send(json.dumps(dict_data) + "\\n") 

def lastline_run_and_return_string(lline):
    try :
        compile(lline,'<stdin>','eval')
        return eval(lline)
    except :
        exec(lline)
    return "None"

def is_assignment(lline):
    return lline.replace("==","..").find('=') != -1
    
def stdout_callback(str):
    socketsend({'type':'stdout','data':str}) 
def stderr_callback(str):
    socketsend({'type':'stderr','data':str}) 

pyconsole = PyodideConsole(__main__.__dict__ ,  stdout_callback= stdout_callback, stderr_callback= stderr_callback, filename="errors") 
print('jey')

jupyter_execution_running = False
verbosity = 1

async def py_onm (event):
  global jupyter_execution_running
  msg = json.loads(event.data)
  if msg['type'] == 'cmd':
    if msg['data'] == 'reload':
     js.location.reload()
  if msg['type'] == 'code':
      jupyter_execution_running = True
      code = msg['code']
      try:

          lines = code.splitlines()
    
          codelines_with_imports = [line for line in lines if 'import' in line]
          codelines_without_imports = [line for line in lines if 'import' not in line]
    
          for line in codelines_with_imports:
            r = await pyconsole.push(line)
                   
          lastline = None
          if len(codelines_without_imports)>0:
              
              if codelines_without_imports[-1].startswith(' ') :
                  pass
              elif is_assignment(codelines_without_imports[-1]):
                  pass
              else:
                  lastline = codelines_without_imports[-1]
                  codelines_without_imports = codelines_without_imports[:-1]

          code_without_imports = "\\n".join(codelines_without_imports)
           
          with open('sourcefile', 'w') as f:
            f.write(code_without_imports)
          r = await pyconsole.push("exec(open('sourcefile','r').read())")
          
          if lastline:
              if verbosity > 0:
                  print('::',lastline)
              #r = lastline_run_and_return_string(lastline)
              r = await pyconsole.push(lastline)
          
          socketsend({'type':'return','data':str(r)})
          
          if verbosity > 0:
              print('r',r)
          
      except Exception as e: 
          stderr_callback(str(e)) 
          with io.StringIO() as buf, redirect_stderr(buf):
                traceback.print_exc()
                output = buf.getvalue()
                stderr_callback(output)
           
          
          socketsend({'type':'cmd','data':'break'})
      jupyter_execution_running = False


  if msg['type'] == 'compl_req':
    if verbosity > 0:
        print(msg)
    completions, start = pyconsole.complete(msg['code'])
    socketsend({'type':'compl_resp','completions':completions , 'start':start,})
    if verbosity > 0:
      print('.')      
 
async def reconnect( unused ):
    global socket
    await sleep(2000)
    socket = WebSocket.new("ws://127.0.0.1:{}/".format(PORT)) 
         
    socket.onmessage = py_onm
    socket.onclose = reconnect
    
socket.onmessage = py_onm
socket.onclose = reconnect


`);
}
main();
