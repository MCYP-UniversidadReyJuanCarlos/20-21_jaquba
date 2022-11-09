import subprocess
import configparser # to read config files
import os
from pathlib import Path
import requests
import logging # to generate traces of execution
import subprocess

#   VARIABLES GLOBALES     #
logger = None # to log application status and info
config = configparser.ConfigParser() # to read config file

files = []

# Print debug messages

def log(str):
    global debug, logger
    if debug is False:
        logger.info(str)
    else:
        print(str)

class Alert():
    ip: str # ip address of the server which get the alert
    module_id: int # id of the alert module which get the alert
    alert_type: str # type of alert
    severity: int # severity of the alert (1 = info, 2 = warning, 3 = error)
    data: str # data of the alert to be sent to the chat

    def run_command(self, command):
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        return iter(p.stdout.readline, b'')

    def send_alert(self, message):
        ip = config['botIP']
        port = config['portIP']
        url = ip + ':' + port + '/alerts'
        response = requests.post(url, message)
        log(response)

def main():
    print('Alert init')
    config.read(Path(__file__).with_name('config.ini'), encoding='iso-8859-1')
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger(__name__)

    if len(files) == 0:
        base_path = Path(__file__).parent.absolute()
        print('base_path', base_path)

        py_file_list = []

        for file_name in base_path.iterdir():
            if file_name.name.endswith('.py') and not file_name.name.endswith(Path(__file__).name):
                # add full path, not just file_name
                py_file_list.append(Path(base_path, file_name.name))

        print('PY files that were found:')
        for i, file_path in enumerate(py_file_list):
            print('\t{:2d} {}'.format(i, file_path))
            files.append(file_path)
            # call script
            subprocess.run(['python', file_path])

if __name__ == '__main__':
    main()