import os
import sys


CURRENTDIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = '/etc/vpnmmanager'
SERVERS_DIR = os.path.join(CONFIG_DIR, 'servers')
AUTH_FILE = '/etc/vpnmmanager/auth.txt'
PID_FILE = '/var/run/vpnmmanager.pid'

sys.path.append(CURRENTDIR)
os.environ['ROOT'] = CURRENTDIR


try:
	from src.vpnhelp import VpnHelp

except ImportError as e:
	print(f"Error: {e}")
	sys.exit(1)


def main() -> None:
	try: 
		vpn = VpnHelp()

		vpn.stop()

		server_file = vpn._get_random_server(SERVERS_DIR)

		process = vpn.start(AUTH_FILE, server_file)

		if process and process.pid:
			with open(PID_FILE, 'w') as f:
				f.write(str(process.pid))
			print(f"Server start with PID: {process.pid}")

		else:
			print(f"Fail")
			sys.exit(1)

	except Exception as err:
		print(f"Error {err}")
		sys.exit(1)


if __name__ == "__main__":
	main()

