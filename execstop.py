import os
import signal
import subprocess
import sys


CURRENTDIR = os.path.dirname(os.path.abspath(__file__))
PID_FILE = '/var/run/vpnmanager.pid'

sys.path.append(CURRENTDIR)
os.environ['ROOT'] = CURRENTDIR


def stop_vpn() -> None:
    try:
        from src.vpnhelp import VpnHelp

        vpn = VpnHelp()
        vpn.stop()

        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)

        print('Stop vpn')

    except Exception as err:
        print(f'Error {err}')
        force_stop()


def force_stop() -> None:
    """Fallback"""
    try:
        #
        if os.path.exists(PID_FILE):
            with open(PID_FILE) as f:
                pid = int(f.read())

            os.kill(pid, signal.SIGTERM)

        # fallback
        subprocess.run(['pkill', 'openvpn'], check=True)

        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)

    except subprocess.CalledProcessError:
        pass

    except Exception as err:
        print(f'Erro: {err}')


if __name__ == '__main__':
    stop_vpn()
