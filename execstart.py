import os
import sys


CURRENTDIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = '/etc/vpnmanager'
SERVERS_DIR = os.path.join(CONFIG_DIR, 'servers')
AUTH_FILE = '/etc/vpnmanager/auth.txt'
PID_FILE = '/var/run/vpnmanager.pid'

sys.path.append(CURRENTDIR)
os.environ['ROOT'] = CURRENTDIR


try:
    from src.filehelp import FileHelp
    from src.vpnhelp import VpnHelp

except ImportError as e:
    print(f'Error: {e}')
    sys.exit(1)


def main() -> None:
    try:
        vpn = VpnHelp()

        vpn.stop()

        server_file = FileHelp.get_random_file(SERVERS_DIR)

        process = vpn.start(AUTH_FILE, server_file)

        if process and process.pid:
            with open(PID_FILE, 'w') as f:
                f.write(str(process.pid))
            print(f'Server start with PID: {process.pid}')

        else:
            print('Fail')
            sys.exit(1)

    except Exception as err:
        print(f'Error {err}')
        sys.exit(1)


if __name__ == '__main__':
    main()
