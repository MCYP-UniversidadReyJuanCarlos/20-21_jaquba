import logging  # to generate traces of execution
import re
import signal
import os
from pathlib import Path

# to create a fastapi (REST) server
from fastapi import FastAPI
from fastapi import Body
import uvicorn

import ssh

#   VARIABLES GLOBALES     #

# to log application status and info
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

api = FastAPI()
debug = True

class Response():
    module_id: int # id of the alert module which get the alert
    alert_type: str # type of alert
    severity: int # severity of the alert (1 = info, 2 = warning, 3 = error)
    data: str # data of the alert
    option: str # action chosen by the user

    def run_command(self, command: str):
        os.system(command)

# Print debug messages
def log(message):
    global debug, logger
    if debug is False:
        logger.info(message)
    else:
        print(message)

@api.post("/response", status_code=200)
async def get_response(response: dict = Body(...)):
    module = response['module']

    if module == 'SSH':
        ssh_module = ssh.SSH()
        ssh_module.execute_response(response)

# Invoked when recieves termination signal from user
def stop_execution(signum, _) -> None:
    log(f'Recibo signal {signum}')
    
# Establish signal to catch when exit requested
def set_signals(handler) -> None:
    if hasattr(signal, 'CTRL_C_EVENT'):
        signal.signal(signal.CTRL_C_EVENT, handler)
    signal.signal(signal.SIGINT, handler)

def main():
    log('Response init')

    uvicorn.run("response:api", host="0.0.0.0", port=5000, log_level="info")

if __name__ == '__main__':
    set_signals(stop_execution)
    main()