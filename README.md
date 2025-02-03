# VPN Manager

VPN Manager is a simple script designed to help manage VPN connections using OpenVPN. It provides additional functionalities like MAC address randomization, daemon configuration, and an installer for easier setup.

## Features

### Implemented Features

- ✅ **File Help**: Class to assist with file management.
- ✅ **MAC Randomization**: Sets a new MAC address before starting the connection with VPN servers.
- ✅ **VPN Help**: Class to assist with VPN configuration management.
- ✅ **Daemon Config**: Configures the daemon for VPN services.
- ✅ **Installer**: Creates an installer for easy script deployment.

### Features in Development

- ⏳ **Implement Logging System**: Improve error handling and monitoring.
- ⏳ **Refactoring of the VPN Help class**: Separate concerns for better code maintainability.

## Installation

To install and use VPN Manager, follow these steps:

### Clone the repository
```bash
git clone https://github.com/thiago-dev-cyber/VPNManager.git
cd VPNManager 
```

### Run the installer
```bash
sudo chmod +x install.sh
sudo ./install.sh
```


If you'd like to use proton's free VPN, follow the steps below:
--
> On the website: https://protonvpn.com/ log in with your account, after logged in click on OpenVPN as shown below:


![Example image](/.github/images/example1.png)

> Then copy the username and password that appears:

![Example image](/.github/images/example2.png)




Right after you need to add your authentication credentials in /etc/vpnmanager/auth.txt

*ps: **Enter the username, then press Enter for the line break and enter the password***

```bash
sudo nano /etc/vpnmanager/auth.txt
```


## Right below we can find a list with several free servers, click on Download to get the settings of the server you want to connect to.

![Example image](/.github/images/example3.png)

You need to put this file in /etc/vpnmanager/servers for the script to be able to find it


## Usage

### To start the VPN service:

```bash
sudo systemctl start vpnmanager.service
```


### To stop the VPN service:

```bash
sudo systemctl stop vpnmanager.service
```


## Requirements

- OpenVPN
- Python >3.9

## Contributing

Contributions are welcome! Feel free to fork the repository and submit a pull request.

## License

This project is licensed under the MIT License.

---

For any questions or issues, feel free to open an issue on GitHub.