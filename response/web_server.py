import json

from response import Response

class WebServer(Response):
    '''
    WebServer response module.
    Options allowed:
        1) Accept connections: allow to process the remote user requests
        2) Rate limit: limit the number of requests which server process from the user
        3) Block IP: block remote user, his requests will be discarded
    '''

    def execute_response(self, response: dict) -> None:
        '''
        Execute the action chosen by the user
        @param response: data recieved from bot
        '''

        data = json.loads(response['data'])
        option = response['option']
        command = None
        ip = data['ip']

        if option == 'block_ip':
            print(f'Bloqueamos las peticiones de la ip {ip}')
            command = f'iptables -I INPUT -s {ip} -p tcp --dport 80 -j DROP'

        elif option == 'ignore':
            print('Aceptamos las conexiones')
        
        if command:
            self.run_command(command)