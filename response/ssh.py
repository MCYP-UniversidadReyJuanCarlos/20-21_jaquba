import json
import subprocess
import shlex
import re

from response import Response

class SSH(Response):
    '''
    SSH response module.
    Options allowed:
        1) Accept connection: permits the remote user to connect
        2) Close connection: end current session of remote user
        3) Block port: block remote user, he cant connect again
    '''

    def get_pids_ssh_connection(self, ip, port):
        '''
        Returns PIDs of incoming SSH conection from ip:port
        '''

        netstat = f'netstat -pnat | grep "{ip}:{port}.*sshd"'
        res_netstat = list(self.run_command_with_output(netstat))
        if len(res_netstat) == 0:
            return None

        ppid = res_netstat[0].split('/')[0].split(' ')[-1]
        print(f'PID: {ppid}')

        ps = f'ps --ppid {ppid} --no-headers'
        ps_res = self.run_command_with_output(ps)

        list_pids = [ppid]
        for line in ps_res:
            list_pids.append(line.split(' ')[0])

        return " ".join(map(str, list_pids))

    def execute_response(self, response: dict) -> None:
        '''
        Execute the action chosen by the user
        @param response: data recieved from bot
        '''

        data = json.loads(response['data'])
        option = response['option']
        command = None
        ip = data['ip']

        if option == 'close_connection':
            port = data['port']
            print(f'Cerramos la conexion con origen {ip}:{port}')

            pids = self.get_pids_ssh_connection(ip, port)
            if pids is None:
                print(f'Ya no esta conectado el origen {ip}:{port}')
                return
            
            print(f'PIDs: {pids}')
            command = f'kill -9 {pids}'

        elif option == 'block_port':
            print(f'Bloqueamos la conexion SSH a la ip {ip}')
            command = f'iptables -A INPUT -s {ip} -p tcp --dport 22 -j DROP'

        elif option == 'ignore':
            print('Aceptamos la conexion')
        
        if command:
            self.run_command(command)