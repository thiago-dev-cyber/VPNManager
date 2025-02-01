import os
import sys


CURRENTDIR = os.path.dirname(os.path.abspath(__file__))

sys.path.append(CURRENTDIR)
os.environ['ROOT'] = CURRENTDIR


from src.vpnhelp import VpnHelp

VPN = VpnHelp()


print(VPN.start('auth.txt','nl-free-75.protonvpn.udp.ovpn'))