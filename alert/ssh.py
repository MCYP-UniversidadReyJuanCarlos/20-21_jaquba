from alert import Alert
import signal
import time
import schedule
import socket
from aiocache import Cache # to save connections already seen
import asyncio # to manage async functions
import json

class Meta:
    def __init__(self):
        pass

    async def get_elem(self, name) -> bool:
        return await cache.get(name, default=False)

    async def set_elem(self, name, value: bool) -> None:
        await cache.set(name, value, 1800)

    async def clear(self) -> bool:
        return await cache.clear()

class SSH(Alert):

    def check_connections(self) -> None:
        global local_ip
        get_active_ssh_cons = 'netstat | grep ssh'
        lines = self.run_command(get_active_ssh_cons)

        for line in lines:
            print(line)

            remote = line.split(' ')[4]
            print(f'New connection from: {remote}')

            remote_addr, remote_port = remote.split(':')
            remote_ip = None

            # check if recieves an IP
            if self.is_valid_ip_address(remote_addr):
                remote_ip = remote_addr
            else:
                # if not, check for hostname
                if remote_addr.endswith('.m'):
                    remote_addr = remote_addr[:remote_addr.index('.m')]
                print(f'hostname: {remote_addr}')

                # get ip address from hostname
                remote_ip = socket.gethostbyname(remote_addr)
            
            print(f'IP: {remote_ip}')

            if asyncio.run(meta.get_elem(remote)) is False:
                alert = {
                    'module_id': 1,
                    'alert_type': 'SSH',
                    'severity': 1,
                    'ip': local_ip,
                    'data': json.dumps({'ip': remote_ip, 'port': remote_port, 'message': 'Nueva conexion SSH'})
                }

                json_data = json.dumps(alert)

                response = self.send_alert(json_data)
                print(response)
                
                asyncio.run(meta.set_elem(remote, True))

    def __init__(self):
        global job_connexions, active
        print('Init alert/ssh module')
        job_connexions = schedule.every(5).seconds.do(self.check_connections)

        while active:
            schedule.run_pending()
            time.sleep(1)

#####     VARIBLES GLOBALES     #####
#####################################
cache = Cache(Cache.MEMORY)
meta = Meta()

active = True
local_ip = socket.gethostbyname(socket.gethostname())
job_connexions = None
#####################################

# Invoked when recieves termination signal from user
def stop_execution(signum, frame) -> None:
    global active, job_connexions
    print('Recibo signal ' + str(signum))
    active = False
    schedule.cancel_job(job_connexions)
    asyncio.run(meta.clear())

# Starts listening
SSH().__init__()

# Establish signal to catch when exit requested
signal.signal(signal.SIGTERM, stop_execution)