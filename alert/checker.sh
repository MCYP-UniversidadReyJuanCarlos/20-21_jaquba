#!/bin/bash

load_config(){

	# Telegram
	TELEGRAM_TOKEN=""
	TELEGRAM_CHAT=""
	TELEGRAM_MESSAGE_ENDPOINT="https://api.telegram.org/bot"$TELEGRAM_TOKEN"/sendMessage?chat_id="$TELEGRAM_CHAT
	TELEGRAM_DOCUMENT_ENDPOINT="https://api.telegram.org/bot"$TELEGRAM_TOKEN"/sendDocument?chat_id="$TELEGRAM_CHAT

	# Other
        DEBUG_MODE=1

    # Send log if error
    	SEND_LOG=1
    	FILE_LOG="/var/log/syslog"

	#Check
		# Ram
		RAM_CRITICAL=90
		RAM_WARNING=80
		# Swap
		SWAP_CRITICAL=90
		SWAP_WARNING=80
		# Disk
		DISK_CRITICAL=90
		DISK_WARNING=80
 		# CPU
		CPU_CRITICAL=90
		CPU_WARNING=80
		# Ping
		PING_HOSTS="google.es;localhost"
		PING_NUMBER=3
		#Processes
		PROCESSES_LIST="ssh;docker"
		# Iptables
		# Ports
		PORTS_LIST="0.0.0.0:ssh"
		# Docker
		DOCKER_CONTAINER_LIST="2cc4c7443c32:Principal;ebc966fdd1e3:Secundario"
		# Users allowed
		MAXUSERS=2
		# System users
		MAX_SYSTEM_USERS=20
}

check_ram(){

	totalRam=$(free -m | awk '/Mem:/ { print $2 }')
	usedRam=$(free -m | awk '/Mem:/ { print $3 }')
	percentRam=$(bc <<< "scale=1; $usedRam*100 / $totalRam")

	if (( ${percentRam%.*} > $RAM_CRITICAL  ))
    then
            send_error " 🔴 CRITICAL 🔴 " "The ram is at $percentRam." "error"
    elif (( ${percentRam%.*} > $RAM_WARNING ))
    then
            send_error " ❕ WARNING ❕ " "The ram is at $percentRam." "error"
    fi


	# Debug mode
	if (( $DEBUG_MODE == 1 ))
	then
                send_error " 📢 DEBUG 📢 " "The ram has been checked: $percentRam%." "debug"
                echo "DEBUG - The ram has been checked: $percentRam%."
	fi
}

check_swap(){

	totalSwap=$(free -m | awk '/Swap:/ { print $2 }')
	freeSwap=$(free -m | awk '/Swap:/ { print $3 }')

	if (( "$totalSwap" > 0 ))
	then
		percentSwap=$(bc <<< "scale=1; $freeSwap*100 / $totalSwap")
	else
		percentSwap=0
	fi

	if (( ${percentSwap%.*} > $SWAP_CRITICAL ))
        then
                send_error " 🔴 CRITICAL 🔴 " "The swap is at $percentSwap." "error"
        elif (( ${percentSwap%.*} > $SWAP_WARNING  ))
	then
                send_error " ❕ WARNING ❕ " "The swap is at $percentSwap." "error"
	fi


	# Debug mode
	if (( $DEBUG_MODE == 1 ))
    then
            send_error " 📢 DEBUG 📢 " "The swap has been checked: $percentSwap %." "debug"
            echo "DEBUG - The swap has been checked: $percentSwap%."
    fi
}


check_disk(){

	percentDisk=$(df -h | grep sd | awk '{print $5}' | sort -n | tail -n 1 | cut -d "%" -f1)

	if (( $(($percentDisk+0)) -ge $DISK_CRITICAL ))
        then
                send_error " 🔴 CRITICAL 🔴 " "HD is at $percentDisk%." "error"
        elif (( $(($percentDisk+0)) -ge $DISK_WARNING  ))
	then
                send_error " ❕ WARNING ❕ " "HD is at $percentDisk%." "error"
	fi


	# Debug mode
	if (( $DEBUG_MODE == 1 ))
        then
                send_error " 📢 DEBUG 📢 " "The disk has been checked: $percentDisk%." "debug"
                echo "DEBUG - The disk has been checked: $percentDisk%."
        fi

}


check_cpu(){

	usedCPU=$(top -bn1 | grep "Cpu(s)" | \
           sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | \
           awk '{print $1}')

    if (( ${usedCPU%.*} > $CPU_CRITICAL ))
        then
        	send_error "🔴 CRITICAL 🔴" "CPU is at $usedCPU%."
        elif (( ${usedCPU%.*} > $CPU_WARNING ))
		then
        	send_error " ❕ WARNING ❕ " "CPU is at $usedCPU%."
	fi


	# Debug mode
    if (( $DEBUG_MODE == 1 ))
    then
            send_error " 📢 DEBUG 📢 " "The CPU has been checked: $usedCPU%." "debug"
            echo "DEBUG - The CPU has been checked: $usedCPU%."
    fi
}


check_ping(){

	hosts=$(echo $PING_HOSTS | tr ";" "\n")

    for host in $hosts
    do

		if ! ping -c $PING_NUMBER $host > /dev/null 
		then
			send_error " 🔴 CRITICAL 🔴 " "Ping to $host has failed." "error"
		fi


		# Debug mode
		if (( $DEBUG_MODE == 1 ))
    	then
            	send_error " 📢 DEBUG 📢 " "The ping to $host has been checked." "debug"
            	echo "DEBUG - The ping to $host has been checked."
    	fi
	done
}


check_processes(){

	processes=$(echo $PROCESSES_LIST | tr ";" "\n")

	for proc in $processes
	do

		running=$(ps ax | grep -v grep | grep $proc | wc -l)

		if (( $running <= 0 ))
		then
			send_error " 🔴 CRITICAL 🔴 " "The $proc process is not running." "error"
		fi


		# Debug mode
		if (( $DEBUG_MODE == 1 ))
		then
			send_error " 📢 DEBUG 📢 " "The $proc process has been checked." "debug"
			echo "DEBUG - The $proc process has been checked."
		fi
	done
}


check_iptables(){

	iptablesUP=$(sudo iptables -n -L -v --line-numbers | egrep "^[0-9]" | wc -l)

	if (( $iptablesUP < 1 ))
        then
        	send_error " 🔴 CRITICAL 🔴 " "Iptables rules are disabled." "error"
        fi


        # Debug mode
        if (( $DEBUG_MODE == 1 ))
        then
        	send_error " 📢 DEBUG 📢 " "It has been checked if the iptables are disabled." "debug"
            echo "DEBUG - It has been checked if the iptables are disabled."
        fi

}


check_ports(){

	ports=$(echo $PORTS_LIST | tr ";" "\n")

	for port in $ports
	do
		if ! netstat -l | grep $port | grep LISTEN > /dev/null
		then
  			send_error " 🔴 CRITICAL 🔴 " "The port [$port] is not open." "error"
		fi


		# Debug mode
		if (( $DEBUG_MODE == 1 ))
		then
			send_error " 📢 DEBUG 📢 " "The port [$port] has been checked." "debug"
			echo "DEBUG - The port [$port] has been checked."
		fi
	done
}


check_docker(){

        containers=$(echo $DOCKER_CONTAINER_LIST | tr ";" "\n")

        for container in $containers
        do

                container_id=$(echo $container | cut -f1 -d":")

                if [ $(docker inspect -f '{{.State.Running}}' $container_id) != "true" ]
                then
                        send_error " 🔴 CRITICAL 🔴 " "The docker container '$container' is not running." "error"
                fi


                # Debug mode
                if (( $DEBUG_MODE == 1 ))
                then
                        send_error " 📢 DEBUG 📢 " "The docker container '$container' has been checked." "debug"
                        echo "DEBUG - The docker container '$container' has been checked."
                fi
        done


}

check_ssh_connections(){
	
	users=$(who | wc -l)
    usersnetstat=$(netstat -natp | grep [0-9][0-9]:22 | wc -l)

	if (($users>MAXUSERS))||(($usersnetstat>MAXUSERS))
	then
        send_error " 🔴 CRITICAL 🔴 " "$users users connected via SSH" "error"
	fi

	# Debug mode
	if (( $DEBUG_MODE == 1 ))
    then
        send_error " 📢 DEBUG 📢 " "The number of users connected via SSH has been checked: $users." "debug"
        echo "DEBUG - The number of users connected via SSH has been checked: $users."
    fi

}



check_system_users(){

		users=$(awk -F: '{ print $1}' /etc/passwd | wc -l)
		    
		if (($users > $MAX_SYSTEM_USERS))
		then
		    send_error " 🔴 CRITICAL 🔴 " "There are more than $MAX_SYSTEM_USERS users in the system: $users." "error"
		fi

		# Debug mode
		if (( $DEBUG_MODE == 1 ))
     	then
            send_error " 📢 DEBUG 📢 " "The number of system users has been checked: $users." "debug"
            echo "DEBUG - The number of system users has been checked: $users."
     	fi
}	


send_error(){

	message="$1 - $2"

	if [ $SEND_LOG == 1 ] && [ "$3" == "error" ]
	then
		$(curl -s -X POST $TELEGRAM_DOCUMENT_ENDPOINT -F document=@"$FILE_LOG" -F caption="$message" > /dev/null)
	elif [ "$3" == "debug" ]
	then
		$(curl -s -X POST $TELEGRAM_MESSAGE_ENDPOINT -F disable_notification=true -F text="$message" > /dev/null)
	else
		$(curl -s -X POST $TELEGRAM_MESSAGE_ENDPOINT -F text="$message" > /dev/null)
	fi
	
}


check() {

	load_config # works
	check_ram # works
	check_swap # works
	check_disk # works
	check_cpu # works
	check_ping # works
	check_processes # works
	check_iptables # works
	check_ports # works
	check_docker # works
	check_system_users #works
}

check
