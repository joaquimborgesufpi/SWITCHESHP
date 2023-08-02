import paramiko
import time
import datetime
import os
#import logging

# Enable debug mode for Netmiko and Paramiko
#logging.basicConfig(level=logging.DEBUG)

vars
vlanid = 'vlantagged'
untagged_vlan = 'vlanuntagged'
namevlan = 'namevlan'
enable_password = "512900" # Change according to the model ['Jinhua1920unauthorized', '512900']
change_password = 'newpassword'
ports_add='ports' # Replace with the desired ports ['GigabitEthernet1/0/', 'GigabitEthernet1/0/2'] 
username_switches = 'userswitch'
password_switches = 'passswitch'
description_port= 'descriptionvlan'
switch_list = [
        {"ip": "ip1"},
        {"ip": "ip2"},
        {"ip": "ip3"},
        {"ip": "ip4"},
        {"ip": "ip5"},
        {"ip": "ip6"},
       # {"ip": "ip7"},
        {"ip": "ip8"}
    ]  # Replace with the IPs version 4 (X.X.X.X) of the switches


def send_command(channel, command, delay=1):
    channel.send(command + '\n')
    time.sleep(delay)

def configure_vlan(ip, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=username, password=password, allow_agent=False, look_for_keys=False)

    channel = ssh.invoke_shell()
    channel.send('_cmdline-mode on\n')
    time.sleep(1)
    output = channel.recv(65535).decode('utf-8')
    if 'Y/N' in output:
        channel.send('y\n')
        time.sleep(1)
        channel.send(f'{enable_password}\n')
        time.sleep(1)

    # Modo Admin
    send_command(channel, "screen-length disable")
    channel.send('system-view\n')
    time.sleep(1)

    send_command(channel, f'{vlanid}')
    send_command(channel, f'des {namevlan}')

    ports = [f'{ports_add}']  # Replace with the desired ports ['GigabitEthernet1/0/1', 'GigabitEthernet1/0/2']
    for port in ports:
        send_command(channel, f'interface {port}')
        send_command(channel, 'port link-type trunk')
        send_command(channel, f'port trunk permit vlan {vlanid}')

    for port in ports:
        send_command(channel, f'interface {port}')
        send_command(channel, f'port trunk pvid vlan {untagged_vlan}')

    for port in ports:
        send_command(channel, f'interface {port}')
        send_command(channel, 'undo port trunk permit vlan 1')

    for port in ports:
        send_command(channel, f'interface {port}') # (channel, 'interface range GigabitEthernet1/0/1 to GigabitEthernet1/0/48')
        send_command(channel, f'description {description_port}')

     # Retrieve current configuration
    output = send_command(channel, 'display current-configuration\n')
    time.sleep(3)
    output = channel.recv(65535).decode('utf-8')
    ssh.close()

    # Print the current configuration
    print('--- Current Configuration ---')
    print(output)
    print('----------------------------')

    print('Switch configured successfully.')

def change_switch_password(ip, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=username, password=password, allow_agent=False, look_for_keys=False)

    channel = ssh.invoke_shell()
    channel.send('_cmdline-mode on\n')
    time.sleep(1)
    output = channel.recv(65535).decode('utf-8')
    if 'Y/N' in output:
        channel.send('y\n')
        time.sleep(1)
        channel.send(f'{enable_password}\n')
        time.sleep(1)

    # Modo admin
    send_command(channel, "screen-length disable")
    channel.send('system-view\n')
    time.sleep(1)
    
    # Change password
    send_command(channel, 'local-user admin')
    send_command(channel, f'password cipher {change_password}')

    # Retrieve current configuration
    output = send_command(channel, 'display current-configuration\n')
    time.sleep(3)

    # Save configuration
    send_command(channel, 'save')
    output = channel.recv(1024).decode('utf-8')
    if 'Y/N' in output:
        channel.send('y\n')
        channel.send('')
        time.sleep(1)
        channel.send('y\n')
        time.sleep(5)

    # Close connection
    ssh.close()

    # Print the current configuration
    print('--- Current Configuration ---')
    print(output)
    print('----------------------------')

    print('Switch configured successfully.')

def backup_switches(switches):
    # Set the current date and time
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M%S")

    # Create a directory for storing the backups
    backup_dir = f"SWITCHESUFPIFLORIANO_{timestamp}"
    os.mkdir(backup_dir)

    # Iterate over the list of switches
    for switch in switches:
        ip_address = switch["ip"]
        filename = f"{backup_dir}/switch_{ip_address}_{timestamp}.txt"

        # Create an SSH client
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # Connect to the switch
            client.connect(ip_address, username=username_switches, password=password_switches)
            channel = client.invoke_shell()

            # Confirm with 'y' for cmdline-mode
            send_command(channel, "_cmdline-mode on", delay=2)
            send_command(channel, "y")

            # Provide enable password
            send_command(channel, enable_password)

            # Send command to enable system-view mode
            send_command(channel, "screen-length disable")
            send_command(channel, "system-view")

            # Send commands to display current-configuration
            send_command(channel, "display current-configuration", delay=10)

            # Receive and handle the output of the command
            output = ""
            while True:
                time.sleep(1)
                if channel.recv_ready():
                    output += channel.recv(65535).decode("utf-8")
                    if "return" in output:
                        break

            # Save the output to a file
            with open(filename, "w") as file:
                file.write(output)

            print(f"Backup for {ip_address} completed successfully.")
        except Exception as e:
            print(f"Error while backing up {ip_address}: {str(e)}")
        finally:
            # Close the SSH connection
            client.close()

def main():

    username = f'{username_switches}'
    password = f'{password_switches}'

    switch_menu = {
        1: configure_vlan,
        2: change_switch_password,
        3: backup_switches,
    }

    while True:
        print("Menu:")
        print("1. Configure VLAN")
        print("2. Change Switch Password")
        print("3. Backup Switches")
        print("0. Exit")
        choice = int(input("Enter your choice: "))

        if choice == 0:
            break

        if choice in switch_menu:
            function = switch_menu[choice]
            if choice == 3:
                function(switch_list)
            else:
                for switch in switch_list:
                    function(switch["ip"], username, password)
                    time.sleep(2)  # Add a delay between configuring each switch (optional)
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main()
