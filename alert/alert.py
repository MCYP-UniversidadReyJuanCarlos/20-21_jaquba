import subprocess

class Alert():
    def __init__(self):
        '''No hace nada '''
    
    def run_command(self, command):
        p = subprocess.call(command, shell=True, stdout=subprocess.PIPE)
        return iter(p.stdout.readline, b'')