import os
import subprocess
import sys
import time


sys.path.append(os.environ['ROOT'])


from .filehelp import FileHelp
from .networkmanager import NetworkManager
from .processhelp import ProcessHelp


class VpnHelp:
    """
    Class responsible for managing vpn startup and shutdown
    """

    def __init__(self):
        self.is_active = False
        self.auth_file = None
        self.config_file = None
        self.system_dns = ['127.0.2.1']
        self.vpn_dns = ['1.1.1.1', '8.8.4.4\n']
        self.openvpn_process = None
        self.server_pool = []

    def start(self, auth_file: str, config_file: str) -> bool:
        """
        Initiates connection to the given vpn server.

        Args:

            auth_file (str): File with username and password for authentication

            config_file (str): File with the certificate and server settings.
        """
        if not os.path.exists(auth_file):
            raise FileNotFoundError(f'Auth file {auth_file} does not exist.')
        if not os.path.exists(config_file):
            raise FileNotFoundError(f'Config file {config_file} does not exist.')

        self.auth_file = auth_file
        self.config_file = config_file

        NetworkManager.disable_kill_switch()
        for attempt in range(3):
            try:
                NetworkManager.new_mac_address()
                # self.new_mac_address()
                self.system_dns = NetworkManager._get_current_dns_server()

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
                if NetworkManager.check_internet_connection():
                    print('VPN started successfully.')

                    NetworkManager.enable_kill_switch()
                    self.is_active = True
                    return self.openvpn_process
                else:
                    self.stop()
                    raise ConnectionError('VPN connection failed.')

            except (
                subprocess.CalledProcessError,
                ConnectionError,
                FileNotFoundError,
            ) as err:
                print(f'Attempt {attempt + 1} failed: {err}')
                self.stop()
                continue

        print('All VPN connection attempts failed.')
        return False

    def stop(self):
        """
        Terminates the connection to the vpn server and kills the process.
        """

        NetworkManager.disable_kill_switch()
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
            ProcessHelp._finish_process('openvpn')
            subprocess.run(
                ['sudo', 'systemctl', 'restart', 'NetworkManager'], check=True
            )
            time.sleep(4)  # Fixed: Use time.sleep
            subprocess.run(
                ['sudo', 'systemctl', 'restart', 'dnscrypt-proxy'], check=True
            )
            subprocess.run(
                ['sudo', 'systemctl', 'restart', 'networking'], check=True
                )
        except subprocess.CalledProcessError as err:
            print(f'Error restarting services: {err}')

        self.is_active = False
        print('VPN stopped.')
