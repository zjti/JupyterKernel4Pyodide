# JupyterKernel4Pyodide
can be used to connect to running pyodode instance via JupyterLab?


## Install Jupyter Kernel

'''
pip install -e ./JupyterKernel4Pyodide
jupyter kernelspec install ./JupyterKernel4Pyodide --user
'''
    
## Test the Kernel with IPythonConsole 

to test this kernel execute the Python Module e.g.:
'''
python -m simplepyodidekernel.SimplePyodideKernel
'''
(this will work if pip install succeded, regardless of the 'jupyter kernelspec' installation)

to test the kernelspec installation:
'''
jupyter-console --kernel JupyterKernel4Pyodide
'''
if this works you should see the new kernel in your jupyter-lab launch menu


## Change the default port for the websocket communication
change in both files: SimplePyodideKernel.py, test.hmtl



    
   
    