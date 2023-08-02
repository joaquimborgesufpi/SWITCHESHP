from netmiko import ConnectHandler
import datetime
import os

# Variáveis de configuração
vlan_id = 'vlanid'
untagged_vlan = 'untaggedvlan'
vlan_name = 'namevlan'
new_user_manager = 'newuser'
tagged_ports = '1-5'  # Exemplo: '1-5'
untagged_ports = '1-5'  # Exemplo: '1-5'
username_switches = 'userswitch'
password_switches = 'passswitch'
acesso_ssh = 'portdeacessossh'

# Lista de switches Aruba 
ips = ["ip1", "ip2", "ip3"]

# Global
switches = [
    {
        "ip": ip,
        "port": acesso_ssh,
        "username": username_switches,
        "password": password_switches,
        "device_type": "hp_procurve",
        "global_delay_factor": 2,
    } for ip in ips
]


def configure_switch(switch):
    try:
        ip = switch['ip']
        # Estabelecer conexão SSH
        net_connect = ConnectHandler(**switch)
        net_connect.enable()  # Entrar no modo privilegiado

        # Entrar no modo administrador
        net_connect.send_command('configure terminal', expect_string=r'#')

        # Criar VLAN com portas etiquetadas
        config_commands = [
            f'{vlan_id}',
            f'{vlan_name}',
            f'{tagged_ports}',
            f'{untagged_vlan}',
            f'{untagged_ports}'
        ]
        net_connect.send_config_set(config_commands)

        # Salvar a configuração em execução em um arquivo
        current_time = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        file_name = f"backup_{ip}_{current_time}.txt"
        output = net_connect.send_command('show running-config structured')
        with open(file_name, 'w') as f:
            f.write(output)

        print(f"Configuração concluída com sucesso para {ip}. Backup salvo como {file_name}")

        net_connect.disconnect()

    except Exception as e:
        print(f"Ocorreu um erro ao configurar {ip}: {str(e)}")


def change_password(device, new_password):
    """Change the password for the user 'manager' on the specified device."""
    try:
        ip = device['ip']
        print(f"Connecting to {ip}...")
        net_connect = ConnectHandler(**device)
        net_connect.enable()
        print(f"Changing password on {ip}...")
        config_commands = [f"password manager user-name {new_user_manager} plaintext {new_password}"]
        net_connect.send_config_set(config_commands)
        net_connect.disconnect()
        print(f"Password changed successfully on {ip}.")

    except Exception as e:
        print(f"An error occurred while changing password on {ip}: {str(e)}")


def backup_running_config(device, filename):
    """Backup the 'show running-config structured' command to a file on the specified device."""
    try:
        ip = device['ip']
        print(f"Connecting to {ip}...")
        net_connect = ConnectHandler(**device)
        print(f"Backing up running-config on {ip}...")
        output = net_connect.send_command("show running-config structured", use_textfsm=True)

        # Create the directory for the backups based on the current date and time
        current_time = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        backup_directory = f"SWITCHESUFPIFLORIANO_{current_time}_{ip}"
        os.makedirs(backup_directory, exist_ok=True)

        # Create the full path for the backup file within the backup directory
        full_path = os.path.join(backup_directory, filename)

        with open(full_path, "w") as f:
            f.write(output)
        net_connect.disconnect()
        print(f"Running-config backed up successfully on {ip} at {full_path}.")

    except Exception as e:
        print(f"An error occurred while backing up running-config on {ip}: {str(e)}")


def main_menu():
    print("Menu:")
    print("1. Configurar switches")
    print("2. Mudar a senha do usuário 'manager'")
    print("3. Fazer backup do running-config")
    print("0. Sair")


def main():
    while True:
        main_menu()
        option = input("Escolha uma opção: ")

        if option == '1':
            for switch in switches:
                configure_switch(switch)
        elif option == '2':
            new_password = input("Digite a nova senha para o usuário 'manager': ")
            for switch in switches:
                change_password(switch, new_password)
        elif option == '3':
            for switch in switches:
                filename = f"{switch['ip']}-{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.txt"
                backup_running_config(switch, filename)
        elif option == '0':
            print("Saindo do programa.")
            break
        else:
            print("Opção inválida. Tente novamente.")


if __name__ == "__main__":
    main()
