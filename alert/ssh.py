
class SSH(Alert):

    def __init__(self):
        super().__init__()
        print('Init alert/ssh module')

        # netstat | grep ssh

        get_active_ssh_cons = 'netstat | grep ssh'

        for line in run_command(get_active_ssh_cons):
            print(line.split())

