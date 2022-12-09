import subprocess

from response import Response

class PerformanceMonitor(Response):
    '''
    PerfMonitor response module.
    Options allowed:
        1) Accept: ignore CPU usage alert
        2) Reboot system: reboot the machine to make fresh start
        3) Power off system: power off the machine 
    '''

    def execute_response(self, response: dict) -> None:
        '''
        Execute the action chosen by the user
        @param response: data recieved from bot
        '''
        option = response['option']
        command = None

        if option == 'reboot':
            print(f'Reiniciamos el equipo')
            command = 'shutdown -r'

        elif option == 'power_off':
            print(f'Apagamos el equipo')
            command = 'shutdown -P'

        elif option == 'ignore':
            print('Aceptamos la alerta sin hacer nada')
        
        if command:
            self.run_command(command)