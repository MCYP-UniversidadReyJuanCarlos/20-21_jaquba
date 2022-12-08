import asyncio  # to manage async functions
import json
import signal
import schedule

from alert import Alert

class PerformanceMonitor(Alert):

    def check_cpu(self) -> None:
        global local_ip
        global threshold_warning_CPU, threshold_critical_CPU
        global sleep_alert_CPU

        get_cpu_usage = 'top -bn1 | grep "Cpu(s)" | awk \'{print $2}\''
        percent_str = list(self.run_command(get_cpu_usage))[0]
        percent = float(percent_str.replace(',', '.'))
        print(f'El uso de CPU es {percent}')

        alert = None
        if percent >= threshold_warning_CPU:
            print(f'WARNING - Se ha excedido el umbral')

            asyncio.run(asyncio.sleep(sleep_alert_CPU*2))
            percent_str = list(self.run_command(get_cpu_usage))[0]
            percent = float(percent_str.replace(',', '.'))

            alert = {
                'module': 'PerfMonitor',
                'alert_type': 'cpu',
                'ip': local_ip,
                'data': json.dumps({'usage': percent})
            }

            if percent >= threshold_critical_CPU:
                print(f'CRITICAL - Supera el umbral critico')
                alert['severity'] = 3
            elif percent >= threshold_warning_CPU:
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
        global threshold_warning_CPU, threshold_critical_CPU
        global sleep_alert_CPU
        global job_cpu, active

        print('Init Alert/PerfMonitor module')

        local_ip = self.get_local_ip()
        print(f'IP local: {local_ip}')
        
        threshold_warning_CPU = int(self.get_config('ALERTS.threshold_warning_CPU'))
        threshold_critical_CPU = int(self.get_config('ALERTS.threshold_critical_CPU'))
        sleep_alert_CPU = float(self.get_config('ALERTS.sleep_alert_CPU'))

        interval = int(self.get_config('ALERTS.interval_CPU'))
        job_cpu = schedule.every(interval).seconds.do(self.check_cpu)

        delay_check = interval/5.0
        while active:
            schedule.run_pending()
            asyncio.run(asyncio.sleep(delay_check))

#####     VARIBLES GLOBALES     #####
#####################################
active = True
job_cpu = None
local_ip = None
threshold_warning_CPU = None
threshold_critical_CPU = None
sleep_alert_CPU = None
#####################################

# Invoked when recieves termination signal from user

def stop_execution(signum, frame) -> None:
    global active, job_cpu
    print(f'Recibo signal {signal}')
    active = False
    schedule.cancel_job(job_cpu)

# Establish signal to catch when exit requested
signal.signal(signal.SIGTERM, stop_execution)

# Starts listening
PerformanceMonitor().__init__()