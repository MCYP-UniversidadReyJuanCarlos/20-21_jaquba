import subprocess
import os
from pathlib import Path
import subprocess

#   VARIABLES GLOBALES     #

files = []

def start():

    if len(files) == 0:
        base_path = Path(__file__).parent.absolute()
        print('base_path', base_path)

        py_file_list = []

        for file_name in base_path.iterdir():
            if file_name.name.endswith('.py') and not file_name.name.endswith(Path(__file__).name) and not file_name.name.endswith('alert.py'):
                # add full path, not just file_name
                py_file_list.append(Path(base_path, file_name.name))

        print('PY files that were found:')
        for i, file_path in enumerate(py_file_list):
            print('\t{:2d} {}'.format(i, file_path))
            files.append(file_path)
            # call script
            subprocess.run(['python', file_path])

start()