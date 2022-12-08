import asyncio  # to manage async functions
import json
import signal

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

            if asyncio.run(meta.get_elem(remote)) is False:
                print(f'New connection from: {remote}')

                remote_addr, remote_port = remote.split(':')
                remote_ip = self.get_ip_from_hostname(remote_addr)
                print(f'IP: {remote_ip}')

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
        global local_ip
        print('Init Alert/SSH module')

        local_ip = self.get_local_ip()
        print(f'IP local: {local_ip}')

        interval = int(self.get_config('ALERTS.interval_SSH'))
        job_connexions = schedule.every(interval).seconds.do(self.check_connections)

        delay_check = interval/5.0
        while active:
            schedule.run_pending()
            asyncio.run(asyncio.sleep(delay_check))

#####     VARIBLES GLOBALES     #####
#####################################
cache = Cache(Cache.MEMORY)
meta = Meta()

active = True
job_connexions = None
local_ip = None
#####################################

# Invoked when recieves termination signal from user
def stop_execution(signum, frame) -> None:
    global active, job_connexions
    print(f'Recibo signal {signal}')
    active = False
    schedule.cancel_job(job_connexions)
    asyncio.run(meta.clear())


# Establish signal to catch when exit requested
signal.signal(signal.SIGTERM, stop_execution)

# Starts listening
SSH().__init__()