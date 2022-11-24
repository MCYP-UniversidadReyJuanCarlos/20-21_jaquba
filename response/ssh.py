import json

from response import Response

class SSH(Response):  

    def execute_response(self, response: dict) -> None:
        data = json.loads(response['data'])
        option = response['option']
        command = None

        if option == 'block_port':
            ip = data['ip']
            print(f'Bloqueamos la conexion de la ip {ip}')
            command = f'iptables -A INPUT -s {ip} -p tcp --dport 22 -j DROP'
        elif option == 'ignore':
            print('Aceptamos la conexion')
        
        if command:
            self.run_command(command)