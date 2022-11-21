import asyncio  # to manage async functions
import json
import signal
import socket

import schedule
from aiocache import Cache  # to save connections already seen

from alert import Alert

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
            remote_ip = self.get_ip_from_hostname(remote_addr)
            print(f'IP: {remote_ip}')

            if asyncio.run(meta.get_elem(remote)) is False:
                print(f'IP 3: {local_ip}')
                alert = {
                    'module': 'SSH',
                    'alert_type': 'new_connection',
                    'severity': 1,
                    'ip': local_ip,
                    'data': json.dumps({'ip': remote_ip, 'port': remote_port})
                }

                json_data = json.dumps(alert)
                response = self.send_alert(json_data)
                print(response)
                if response.status_code == 201:
                    asyncio.run(meta.set_elem(remote, True))
                else:
                    print('Error al enviar alerta')

    def __init__(self):
        global job_connexions, active
        print('Init alert/ssh module')
        job_connexions = schedule.every(5).seconds.do(self.check_connections)

        while active:
            schedule.run_pending()
            asyncio.run(asyncio.sleep(1))

#####     VARIBLES GLOBALES     #####
#####################################
cache = Cache(Cache.MEMORY)
meta = Meta()

active = True
job_connexions = None
#####################################

# Invoked when recieves termination signal from user
def stop_execution(signum, frame) -> None:
    global active, job_connexions
    print(f'Recibo signal {signal}')
    active = False
    schedule.cancel_job(job_connexions)
    asyncio.run(meta.clear())

def get_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

# Establish signal to catch when exit requested
signal.signal(signal.SIGTERM, stop_execution)

local_ip = get_ip()

# Starts listening
SSH().__init__()