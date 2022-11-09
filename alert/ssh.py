from alert import Alert
import time

class SSH(Alert):

    def __init__(self):
        print('Init alert/ssh module')
        # netstat | grep ssh
        get_active_ssh_cons = 'netstat | grep ssh'

        for line in self.run_command(get_active_ssh_cons):
            print(line)
            #response = this.send_alert(line)
            #print(response)
            time.sleep(5)

SSH().__init__()