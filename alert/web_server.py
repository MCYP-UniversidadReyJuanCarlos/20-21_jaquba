import asyncio  # to manage async functions
import json
import signal
import schedule
from collections import Counter

from alert import Alert

class WebServer(Alert):

    def check_http_404(self) -> None:
        global local_ip
        global interval, threshold_warning_HTTP, threshold_critical_HTTP

        get_http_404 = f'awk -v d1="$(date --date \'-{interval} min\' \'+%d/%b/%Y:%T\')" ' \
            + '\'{gsub(/^[\[\t]+/, "", $4);}; $4 > d1\' /var/log/nginx/access.log ' \
            + '| grep 404 | awk \'{print $1}\''

        ocurrencies = Counter(self.run_command(get_http_404))
        print(f'Se encuentran las peticiones: {ocurrencies}')

        for ip in ocurrencies:
            count = ocurrencies[ip]
            print(f'IP: {ip} count = {count}')

            alert = {
                'module': 'WebServer',
                'alert_type': 'http_404',
                'ip': local_ip,
                'data': json.dumps({'ip': ip, 'count': count, 'interval': interval})
            }

            if count >= threshold_critical_HTTP:
                print(f'CRITICAL - Supera el umbral critico')
                alert['severity'] = 3
            elif count >= threshold_warning_HTTP:
                print(f'WARNING - Supera el umbral de alerta')
                alert['severity'] = 2
            else:
                alert = None

            if alert:
                json_data = json.dumps(alert)
                response = self.send_alert(json_data)
                print(f'Alerta enviada, respuesta = {response}')

                if response.status_code != 201:
                    print('Error al enviar alerta')

    def __init__(self):
        global local_ip
        global interval, threshold_warning_HTTP, threshold_critical_HTTP
        global job_http_404, active

        print('Init Alert/WebServer module')

        local_ip = self.get_local_ip()
        print(f'IP local: {local_ip}')
        
        threshold_warning_HTTP = int(self.get_config('ALERTS.threshold_warning_HTTP'))
        threshold_critical_HTTP = int(self.get_config('ALERTS.threshold_critical_HTTP'))

        interval = int(self.get_config('ALERTS.interval_HTTP'))
        job_http_404 = schedule.every(interval).minutes.do(self.check_http_404)

        delay_check = interval*60/5.0 # we have minutes, need delay in seconds
        while active:
            schedule.run_pending()
            asyncio.run(asyncio.sleep(delay_check))

#####     VARIBLES GLOBALES     #####
#####################################
active = True
job_http_404 = None
local_ip = None
interval = None
threshold_warning_HTTP = None
threshold_critical_HTTP = None
#####################################

# Invoked when recieves termination signal from user

def stop_execution(signum, frame) -> None:
    global active, job_http_404
    print(f'Recibo signal {signal}')
    active = False
    schedule.cancel_job(job_http_404)

# Establish signal to catch when exit requested
signal.signal(signal.SIGTERM, stop_execution)

# Starts listening
WebServer().__init__()