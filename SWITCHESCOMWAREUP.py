import paramiko
import time
import datetime
import os

# Defina as variáveis de configuração aqui
vlanid = 'vlantagged'
untagged_vlan = 'vlanuntagged'
namevlan = 'namevlan'
enable_password = "512900"  # Change according to the model ['Jinhua1920unauthorized', '512900']
change_password = 'newpassword'
ports_add = ['ports']  # Replace with the desired ports ['GigabitEthernet1/0/', 'GigabitEthernet1/0/2']
username_switches = 'userswitch'
password_switches = 'passswitch'
description_port = 'descriptionvlan'
switch_list = [
    {"ip": "ip1"},
    {"ip": "ip2"},
    {"ip": "ip3"},
    {"ip": "ip4"},
    {"ip": "ip5"},
    {"ip": "ip6"},
    {"ip": "ip8"}
]  # Replace with the IPs version 4 (X.X.X.X) of the switches


def send_command(channel, command, delay=1):
    channel.send(command + '\n')
    time.sleep(delay)


def configure_vlan(ssh, ip):
    channel = ssh.invoke_shell()
    send_command(channel, '_cmdline-mode on')
    time.sleep(1)
    output = channel.recv(65535).decode('utf-8')
    if 'Y/N' in output:
        send_command(channel, 'y')
        time.sleep(1)
        send_command(channel, f'{enable_password}')
        time.sleep(1)

    # Modo Admin
    send_command(channel, "screen-length disable")
    send_command(channel, 'system-view')

    send_command(channel, f'{vlanid}')
    send_command(channel, f'des {namevlan}')

    # Configurar portas
    for port in ports_add:
        send_command(channel, f'interface {port}')
        send_command(channel, 'port link-type trunk')
        send_command(channel, f'port trunk permit vlan {vlanid}')
        send_command(channel, f'port trunk pvid vlan {untagged_vlan}')
        send_command(channel, 'undo port trunk permit vlan 1')
        send_command(channel, f'description {description_port}')

    # Retrieve current configuration
    send_command(channel, 'display current-configuration')
    time.sleep(3)
    output = channel.recv(65535).decode('utf-8')

    # Print the current configuration
    print(f'--- Current Configuration for {ip} ---')
    print(output)
    print('----------------------------')


def change_switch_password(ssh, ip):
    channel = ssh.invoke_shell()
    send_command(channel, '_cmdline-mode on')
    time.sleep(1)
    output = channel.recv(65535).decode('utf-8')
    if 'Y/N' in output:
        send_command(channel, 'y')
        time.sleep(1)
        send_command(channel, f'{enable_password}')
        time.sleep(1)

    # Modo admin
    send_command(channel, "screen-length disable")
    send_command(channel, 'system-view')

    # Change password
    send_command(channel, 'local-user admin')
    send_command(channel, f'password cipher {change_password}')

    # Retrieve current configuration
    send_command(channel, 'display current-configuration')
    time.sleep(3)
    output = channel.recv(65535).decode('utf-8')

    # Save configuration
    send_command(channel, 'save')
    output = channel.recv(1024).decode('utf-8')
    if 'Y/N' in output:
        send_command(channel, 'y')
        time.sleep(1)
        send_command(channel, '')
        time.sleep(1)
        send_command(channel, 'y')
        time.sleep(5)

    # Print the current configuration
    print(f'--- Current Configuration for {ip} ---')
    print(output)
    print('----------------------------')


def backup_switch(ssh, ip):
    # Set the current date and time
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M%S")

    # Create a directory for storing the backups
    backup_dir = f"SWITCHESUFPIFLORIANO_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)

    filename = f"{backup_dir}/switch_{ip}_{timestamp}.txt"

    channel = ssh.invoke_shell()

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

    print(f"Backup for {ip} completed successfully.")


def main():
    switch_menu = {
        1: configure_vlan,
        2: change_switch_password,
        3: backup_switch,
    }

    # Create a single SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(username=username_switches, password=password_switches)
        for switch in switch_list:
            ip = switch["ip"]
            choice = int(input(f"Menu for Switch {ip}:\n1. Configure VLAN\n2. Change Switch Password\n3. Backup Switch\n0. Exit\nEnter your choice: "))

            if choice == 0:
                break

            if choice in switch_menu:
                function = switch_menu[choice]
                function(ssh, ip)
            else:
                print("Invalid choice. Please try again.")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        ssh.close()


if __name__ == '__main__':
    main()
