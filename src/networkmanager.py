import random
import subprocess
import sys
import time


class NetworkManager:
    """
    Class to assist with tasks related to network management.
    """

    @staticmethod
    def _generate_vendor_mac() -> str:
        """
        Generates a MAC address using known vendor OUIs
        """

        # List of common virtual machine and device OUIs
        VENDOR_OUI = [
            '00:0C:29',  # VMware
            '08:00:27',  # VirtualBox
            '00:1C:42',  # Parallels
            '00:15:5D',  # Hyper-V
            '00:16:3E',  # Xen
            '00:23:AE',  # Dell
            'A4:4C:C8',  # Intel
        ]
        oui = random.choice(VENDOR_OUI)

        random_part = [random.randint(0x00, 0xFF) for _ in range(3)]

        mac = (
            f'{oui}:',
            f'{random_part[0]:02X}',
            f':{random_part[1]:02X}',
            f':{random_part[2]:02X}'.lower(),
        )

        return ''.join(mac)

    @staticmethod
    def _get_network_interfaces() -> list:
        """
        Filters only relevant physical interfaces
        """
        try:
            result = subprocess.run(
                ['ip', '-o', 'link', 'show'], capture_output=True, text=True, check=True
            )
            interfaces = []
            for line in result.stdout.split('\n'):
                if 'link/ether' in line and 'state UP' in line:
                    parts = line.split(': ')
                    if len(parts) > 1:
                        interface = parts[1].split()[0]
                        if not any(
                            invalid in interface
                            for invalid in ['lo', 'docker', 'virbr', 'veth']
                        ):
                            interfaces.append(interface)
            return interfaces

        except subprocess.CalledProcessError as e:
            print(f'Error getting interfaces: {e}')
            return []

    @staticmethod
    def _restart_network():
        """
        Restarts network services to ensure new MAC application
        """
        try:
            subprocess.run(
                ['sudo', 'systemctl', 'restart', 'NetworkManager'], check=True
            )
            time.sleep(5)
        except subprocess.CalledProcessError as e:
            print(f'Warning: Failed to restart NetworkManager: {e}')

    @staticmethod
    def _renew_dhcp(interface: str):
        """
        Attempts to renew DHCP lease

        Args:

            interface (str): Name from Inteface e.g eth1
        """
        try:
            subprocess.run(['sudo', 'dhclient', '-r', interface], check=True)
            subprocess.run(['sudo', 'dhclient', interface], check=True)
            time.sleep(5)

        except subprocess.CalledProcessError as e:
            print(f'Error renewing DHCP: {e}')

    @staticmethod
    def new_mac_address(max_attempts: int = 5, wait_time: int = 10) -> bool:
        """
        Improved implementation for MAC address rotation

        Args:

            max_attempts (int): Maximum number of attempts

            wait_time (int): Maximum number of seconds which script will wait.
        """
        try:
            interfaces = NetworkManager._get_network_interfaces()
            if not interfaces:
                print('No suitable network interfaces found!')
                return False

            for interface in interfaces:
                print(f'Working on interface: {interface}')

                for attempt in range(1, max_attempts + 1):
                    new_mac = NetworkManager._generate_vendor_mac()
                    print(f'Attempt {attempt}/{max_attempts} - New MAC: {new_mac}')

                    try:
                        # Deactivate interface
                        subprocess.run(
                            ['sudo', 'ip', 'link', 'set', 'dev', interface, 'down'],
                            check=True,
                        )

                        # Change MAC
                        subprocess.run(
                            [
                                'sudo',
                                'ip',
                                'link',
                                'set',
                                'dev',
                                interface,
                                'address',
                                new_mac,
                            ],
                            check=True,
                            stderr=subprocess.DEVNULL,
                        )

                        # Reactivate interface
                        subprocess.run(
                            ['sudo', 'ip', 'link', 'set', 'dev', interface, 'up'],
                            check=True,
                        )

                        # Wait for stabilization
                        time.sleep(3)

                        # Restart network services
                        NetworkManager._restart_network()

                        # Renew DHCP
                        NetworkManager._renew_dhcp(interface)

                        # Check connection with longer timeout
                        if NetworkManager.check_internet_connection(timeout=15):
                            print(
                                'Connection successfully'
                                + f'established using MAC: {new_mac}'
                            )
                            return True

                    except subprocess.CalledProcessError as e:
                        print(f'Network operation error: {e}')
                        continue

                    # Progressive wait between attempts
                    time.sleep(wait_time * attempt)

            print('All attempts failed. Considering full reboot.')
            return False

        except Exception as e:
            print(f'Critical error: {str(e)}')
            return False

    @staticmethod
    def check_internet_connection(timeout: int = 10) -> bool:
        """
        Improved connection check

        Args:

            timeout (int): Maximum Standby Time.
        """
        try:
            # Test both ping and DNS
            ping = subprocess.run(
                ['ping', '-c', '2', '-W', str(timeout), '1.1.1.1'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            dns = subprocess.run(
                ['nslookup', 'google.com'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            return ping.returncode == 0 and dns.returncode == 0

        except Exception:
            return False

    @staticmethod
    def _get_current_dns_server() -> list:
        """
        Picks up the system's current dns server.
        """
        try:
            dns_servers = []

            with open('/etc/resolv.conf') as file:
                for line in file:
                    if line.startswith('nameserver'):
                        dns_servers.append(line.split()[1])

        except Exception as err:
            print(f'Error reading DNS config: {err}')

        return list(set(dns_servers))

    @staticmethod
    def enable_kill_switch():
        """
        Enable kill switch with iptables firewall
        """
        try:
            # backup current iptables config.
            subprocess.run(
                'iptables-save > /etc/iptables/iptables_backup', shell=True, check=True
            )

            # Warning del current iptables config.
            subprocess.run(['iptables', '--flush'], check=True)
            subprocess.run(['iptables', '--delete-chain'], check=True)

            subprocess.run(
                ['iptables', '-A', 'OUTPUT', '-o', 'lo', '-j', 'ACCEPT'], check=True
            )
            subprocess.run(
                [
                    'iptables',
                    '-A',
                    'OUTPUT',
                    '-m',
                    'conntrack',
                    '--ctstate',
                    'ESTABLISHED,RELATED',
                    '-j',
                    'ACCEPT',
                ],
                check=True,
            )

            subprocess.run(
                ['iptables', '-A', 'OUTPUT', '-o', 'tun0', '-j', 'ACCEPT'], check=True
            )

            subprocess.run(['iptables', '-P', 'OUTPUT', 'DROP'], check=True)

            print('Kill switch enable.')

        except subprocess.CalledProcessError as e:
            print(f'Error to config iptables: {e}')
            sys.exit(1)

    @staticmethod
    def disable_kill_switch():
        """
        Disable killswitch
        """
        try:
            subprocess.run(
                'iptables-restore < /etc/iptables/iptables_backup',
                shell=True,
                check=True,
            )
            print('Kill switch disable.')
        except subprocess.CalledProcessError as e:
            print(f'Error to restuart iptables: {e}')
