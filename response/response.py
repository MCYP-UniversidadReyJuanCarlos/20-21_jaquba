import logging  # to generate traces of execution
import re
import signal
import subprocess
import shlex
from pathlib import Path

# to create a fastapi (REST) server
from fastapi import FastAPI
from fastapi import Body
import uvicorn

#   VARIABLES GLOBALES     #

# to log application status and info
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

api = FastAPI()
debug = True

def log(message: str):
    ''' Print debug messages '''
    global debug, logger
    if debug is False:
        logger.info(message)
    else:
        print(message)

class Response():
    module_id: int # id of the alert module which get the alert
    alert_type: str # type of alert
    severity: int # severity of the alert (1 = info, 2 = warning, 3 = error)
    data: str # data of the alert
    option: str # action chosen by the user

    def run_command(self, command: str):
        '''
        Execute command without reading the output
        '''
        subprocess.call(shlex.split(command))

    def run_command_with_output(self, command: str):
        '''
        Execute command reading the output and dealing with pipes inside command
        @param command: the command to execute
        @return a iterable of lines returned by command
        '''

        list_commands = [command]
        if '|' in command:
            list_commands = list(map(str.strip, command.split('|')))

        command_0_split = shlex.split(list_commands[0])
        log(f'Command 0: {command_0_split}')
        p = subprocess.Popen(command_0_split, stdout=subprocess.PIPE)

        previous_p = p
        for command_i in list_commands[1:]:
            command_i_split = shlex.split(command_i)
            log(f'Command: {command_i_split}')
            previous_p = subprocess.Popen(command_i_split, stdin=previous_p.stdout, stdout=subprocess.PIPE)

        output = previous_p.communicate()[0].decode("utf-8")

        for line in output.split('\n'):
            line = line.strip()
            line = re.sub(' +', ' ', line)
            yield line

@api.post("/response", status_code=200)
async def get_response(response: dict = Body(...)):
    ''' 
    API REST:
    Recieve responses from user and make the action requested
    using the corresponding module

    @param response: alert data plus selected option
    @return: HTTP 200 if action was made
    '''

    module = response['module']

    if module == 'SSH':
        import ssh
        ssh_module = ssh.SSH()
        ssh_module.execute_response(response)
    if module == 'PerfMonitor':
        import perf_monitor
        perf_monitor = perf_monitor.PerformanceMonitor()
        perf_monitor.execute_response(response)

def stop_execution(signum, _) -> None:
    ''' Invoked when recieves termination signal from user '''
    log(f'Recibo signal {signum}')
    
def set_signals(handler) -> None:
    ''' Establish signal to catch when exit requested '''
    if hasattr(signal, 'CTRL_C_EVENT'):
        signal.signal(signal.CTRL_C_EVENT, handler)
    signal.signal(signal.SIGINT, handler)

def main():
    log('Response init')

    uvicorn.run("response:api", host="0.0.0.0", port=5000, log_level="info")

if __name__ == '__main__':
    set_signals(stop_execution)
    main()