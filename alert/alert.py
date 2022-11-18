import configparser # to read config files
import os
from pathlib import Path
import logging # to generate traces of execution
import subprocess
import requests
import socket
import signal
import re

#   VARIABLES GLOBALES     #

# to log application status and info
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
debug = True
config = configparser.ConfigParser() # to read config file
config.read(Path(__file__).with_name('config.ini'), encoding='iso-8859-1')
files = []

# Print debug messages
def log(message):
    global debug, logger
    if debug is False:
        logger.info(message)
    else:
        print(message)

def is_valid_ipv4_address(address):
    try:
        socket.inet_pton(socket.AF_INET, address)
    except AttributeError:  # no inet_pton here, sorry
        try:
            socket.inet_aton(address)
        except socket.error:
            return False
        return address.count('.') == 3
    except socket.error:  # not a valid address
        return False
    return True

def is_valid_ipv6_address(address):
    try:
        socket.inet_pton(socket.AF_INET6, address)
    except socket.error:  # not a valid address
        return False
    return True

class Alert():
    ip: str # ip address of the server which get the alert
    module_id: int # id of the alert module which get the alert
    alert_type: str # type of alert
    severity: int # severity of the alert (1 = info, 2 = warning, 3 = error)
    data: str # data of the alert to be sent to the chat

    def run_command(self, command: str):
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        for line in iter(p.stdout.readline, b''):
            line = line.decode("utf-8").replace('\n', '')
            line = re.sub(' +', ' ', line)
            yield line

    def send_alert(self, message: str):
        global config
        ip = config['BOT']['ip']
        port = config['BOT']['port']
        url = f'http://{ip}:{port}/alert'
        log(f'New alert to send {message}')
        
        headers = {
            'User-Agent': 'pythonAlertClass',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        response = requests.post(url, headers=headers, data=message)
        log(response)
        return response

    def is_valid_ip_address(self, address: str) -> bool:
        return is_valid_ipv4_address(address) or is_valid_ipv6_address(address)


# Invoked when recieves termination signal from user
def stop_execution(signum, _) -> None:
    log(f'Recibo signal {signum}')
    ps = subprocess.Popen(f'ps -o pid --ppid {os.getpid()} --noheaders', shell=True, stdout=subprocess.PIPE)
    for p in iter(ps.stdout.readline, b''):
        p = p.decode("utf-8").replace('\n', '')
        p = re.sub(' +', ' ', p)
        log(p)
        os.kill(int(p), signal.SIGTERM)

# Establish signal to catch when exit requested
def set_signals(handler) -> None:
    if hasattr(signal, 'CTRL_C_EVENT'):
        signal.signal(signal.CTRL_C_EVENT, handler)
    signal.signal(signal.SIGINT, handler)

def main():
    global files
    log('Alert init')

    log('Config file: ' + str(config))
    log({section: dict(config[section]) for section in config.sections()})

    if len(files) == 0:
        base_path = Path(__file__).parent.absolute()
        log(f'base_path {base_path}')
        
        for file_name in base_path.iterdir():
            if file_name.name.endswith('.py') and not file_name.name.endswith(Path(__file__).name):
                # add full path, not just file_name
                file_path = Path(base_path, file_name.name)
                if file_path not in files:
                    log(f'New file:\t{file_path}')
                    files.append(file_path)
                    # call script
                    subprocess.run(['python', file_path])
        
        '''
        py_file_list = []
        for file_name in base_path.iterdir():
            if file_name.name.endswith('.py') and not file_name.name.endswith(Path(__file__).name):
                # add full path, not just file_name
                py_file_list.append(Path(base_path, file_name.name))

        print('PY files that were found:')
        for i, file_path in enumerate(py_file_list):
            print('\t{:2d} {}'.format(i, file_path))
            # call script
            subprocess.run(['python', file_path])
        '''

if __name__ == '__main__':
    set_signals(stop_execution)
    main()