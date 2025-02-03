import os
import random
import subprocess
import sys
import time
from typing import List, Optional


sys.path.append(os.environ['ROOT'])


from .filehelp import FileHelp


class VpnHelp:
    def __init__(self):
        self.is_active = False
        self.auth_file: Optional[str] = None
        self.config_file: Optional[str] = None
        self.system_dns: List[str] = ['127.0.2.1']
        self.vpn_dns: List[str] = ['1.1.1.1', '8.8.4.4\n']
        self.openvpn_process: Optional[subprocess.Popen] = None
        self.server_pool = []

    def _generate_vendor_mac(self) -> str:
        """Generates a MAC address using known vendor OUIs"""
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

    def __get_network_interfaces(self) -> List[str]:
        """Filters only relevant physical interfaces"""
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

    def __restart_network(self):
        """Restarts network services to ensure new MAC application"""
        try:
            subprocess.run(
                ['sudo', 'systemctl', 'restart', 'NetworkManager'], check=True
            )
            time.sleep(5)
        except subprocess.CalledProcessError as e:
            print(f'Warning: Failed to restart NetworkManager: {e}')

    def __renew_dhcp(self, interface: str):
        """Attempts to renew DHCP lease"""
        try:
            subprocess.run(['sudo', 'dhclient', '-r', interface], check=True)
            subprocess.run(['sudo', 'dhclient', interface], check=True)
            time.sleep(5)
        except subprocess.CalledProcessError as e:
            print(f'Error renewing DHCP: {e}')

    def new_mac_address(self, max_attempts: int = 5, wait_time: int = 10) -> bool:
        """Improved implementation for MAC address rotation"""
        try:
            interfaces = self.__get_network_interfaces()
            if not interfaces:
                print('No suitable network interfaces found!')
                return False

            for interface in interfaces:
                print(f'Working on interface: {interface}')

                for attempt in range(1, max_attempts + 1):
                    new_mac = self._generate_vendor_mac()
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
                        self.__restart_network()

                        # Renew DHCP
                        self.__renew_dhcp(interface)

                        # Check connection with longer timeout
                        if self.check_internet_connection(timeout=15):
                            print(
                                'Connection successfully'
                                + 'established using MAC: {new_mac}'
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

    def check_internet_connection(self, timeout: int = 10) -> bool:
        """Improved connection check"""
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

    def _get_current_dns_server(self) -> List[str]:
        try:
            dns_servers = []

            with open('/etc/resolv.conf') as file:
                for line in file:
                    if line.startswith('nameserver'):
                        dns_servers.append(line.split()[1])

        except Exception as err:
            print(f'Error reading DNS config: {err}')

        return list(set(dns_servers))

    @classmethod
    def __finish_process(cls, process_name: str):
        try:
            subprocess.run(['sudo', 'killall', process_name], check=True)

        except subprocess.CalledProcessError:
            print(f'It was not possible to close the process {process_name}')

    def start(self, auth_file: str, config_file: str) -> bool:
        if not os.path.exists(auth_file):
            raise FileNotFoundError(f'Auth file {auth_file} does not exist.')
        if not os.path.exists(config_file):
            raise FileNotFoundError(f'Config file {config_file} does not exist.')

        self.auth_file = auth_file
        self.config_file = config_file

        for attempt in range(3):
            try:
                self.new_mac_address()
                self.system_dns = self._get_current_dns_server()

                # Write VPN DNS to resolv.conf
                dns_content = '\n'.join([f'nameserver {dns}' for dns in self.vpn_dns])
                FileHelp.write('/etc/resolv.conf', dns_content)

                # Start OpenVPN and wait for connection
                self.openvpn_process = subprocess.Popen(
                    [
                        'sudo',
                        'openvpn',
                        '--config',
                        config_file,
                        '--auth-user-pass',
                        auth_file,
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

                # Wait for VPN connection to establish
                time.sleep(10)
                if self.check_internet_connection():
                    print('VPN started successfully.')
                    self.is_active = True
                    return self.openvpn_process
                else:
                    self.stop()
                    raise ConnectionError('VPN connection failed.')

            except (
                subprocess.CalledProcessError,
                ConnectionError,
                FileNotFoundError,
            ) as e:
                print(f'Attempt {attempt + 1} failed: {e}')
                self.stop()
                continue

        print('All VPN connection attempts failed.')
        return False

    def stop(self):
        # Terminate OpenVPN process
        if self.openvpn_process:
            self.openvpn_process.terminate()
            try:
                self.openvpn_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.openvpn_process.kill()

        # Restore original DNS settings
        if self.system_dns:
            dns_content = '\n'.join([f'nameserver {dns}' for dns in self.system_dns])
            FileHelp.write('/etc/resolv.conf', dns_content)
        else:
            FileHelp.write('/etc/resolv.conf', 'nameserver 1.1.1.1\n')  # Fallback

        try:
            self.__finish_process('openvpn')
            subprocess.run(
                ['sudo', 'systemctl', 'restart', 'NetworkManager'], check=True
            )
            time.sleep(4)  # Fixed: Use time.sleep
            subprocess.run(
                ['sudo', 'systemctl', 'restart', 'dnscrypt-proxy'], check=True
            )
        except subprocess.CalledProcessError as e:
            print(f'Error restarting services: {e}')

        self.is_active = False
        print('VPN stopped.')

    def _get_random_server(self, path: str):
        try:
            if not os.path.exists(path) or not os.path.isdir(path):
                raise FileNotFoundError('Directory not found, check the path entered')

            if not self.server_pool:
                servers = []

                for serve in os.listdir(path):
                    full_path = os.path.join(path, serve)
                    if os.path.isfile(full_path):
                        servers.append(full_path)

                self.server_pool = servers

            server_file = random.choice(self.server_pool)
            return server_file

        except Exception as err:
            print(err)
