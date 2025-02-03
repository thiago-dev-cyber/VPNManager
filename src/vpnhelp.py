import os
import random
import subprocess
import sys
import time


sys.path.append(os.environ['ROOT'])


from .filehelp import FileHelp


class VpnHelp:
    def __init__(self):
        self.is_active = False
        self.auth_file = None
        self.config_file = None
        self.system_dns = ['127.0.2.1']
        self.vpn_dns = ['1.1.1.1', '8.8.4.4\n']
        self.openvpn_process = None
        self.server_pool = []


    # TODO: Create a new class and add this method
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



