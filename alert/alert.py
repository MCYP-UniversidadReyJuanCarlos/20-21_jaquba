import configparser  # to read config files
import logging  # to generate traces of execution
import os
import re
import signal
import socket
import shlex
import subprocess
from pathlib import Path

import requests

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

    def get_config(self, key: str) -> str:
        global config

        value = None
        for subkey in key.split('.'):
            if value is None:
                value = config[subkey]
            else:
                value = value[subkey]
        
        return value

    def run_command(self, command: str):
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        for line in iter(p.stdout.readline, b''):
            line = line.decode("utf-8").replace('\n', '')
            line = re.sub(' +', ' ', line)
            yield line

    def send_alert(self, message: str) -> requests.Response:
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
        return response

    def is_valid_ip_address(self, address: str) -> bool:
        return is_valid_ipv4_address(address) or is_valid_ipv6_address(address)
    
    def get_ip_from_hostname(self, remote_addr: str) -> str:
        remote_ip = None

        # check if recieves an IP
        if self.is_valid_ip_address(remote_addr):
            remote_ip = remote_addr
        else:
            # if not, check for hostname
            if remote_addr.endswith('.m'):
                remote_addr = remote_addr[:remote_addr.index('.m')]
            log(f'hostname: {remote_addr}')

            # get ip address from hostname
            remote_ip = socket.gethostbyname(remote_addr)
        
        return remote_ip
    
    def get_local_ip(self) -> str:
        log('get_local_ip')
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
            log(f'IP socket: {IP}')
        except Exception:
            IP = '127.0.0.1'
            log(f'Exception, IP: {IP}')
        finally:
            s.close()
        return IP


# Invoked when recieves termination signal from user
def stop_execution(signum, _) -> None:
    log(f'Recibo signal {signum}')
    curr_pid = os.getpid()
    log(f'Current PID: {curr_pid}')
    ps = subprocess.Popen(shlex.split(f'ps -o pid --ppid {curr_pid} --noheaders'), stdout=subprocess.PIPE)
    for p in iter(ps.stdout.readline, b''):
        p = p.decode("utf-8").replace('\n', '')
        p = re.sub(' +', ' ', p)
        os.kill(int(p), signal.SIGTERM)
        log(f'Kill PID {p}')

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
        
        processes = []

        for file_path in base_path.iterdir():
            file_name = file_path.name
            if file_name.endswith('.py') and not file_name.endswith(Path(__file__).name):
                if file_path not in files:
                    log(f'New file:\t{file_path}')
                    files.append(file_path)
                    # call script
                    p = subprocess.Popen(['python3', file_path])
                    log(f'PID:\t{p.pid}')
                    processes.append(p)

        for p in processes:
            log(f'Wait PID:\t{p.pid}')
            p.wait()

if __name__ == '__main__':
    set_signals(stop_execution)
    main()