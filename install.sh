#!/usr/bin/env bash
set -euo pipefail

# ============ CONSTANTS ================
DEST_DIR="/opt/vpnmanager"
SERVICE_NAME="vpnmanager.service"
CONFIG_DIR="/etc/vpnmanager"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RESET='\033[0m'

# Function to check for errors.
check_errors() {
  if [ "$?" -ne 0 ]; then
    echo -e "${RED}Error: $1${RESET}"
    exit 1
  fi
}

# Check if script is run as root.
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}This script must be run as ROOT.${RESET}"
  exit 1
fi

# Create the destination directory if it does not exist.
if [ ! -d "${DEST_DIR}" ]; then
  echo -e "${GREEN}[+] Creating directory ${DEST_DIR}.${RESET}"
  mkdir -p "${DEST_DIR}"
  check_errors "Failed to create directory ${DEST_DIR}"
fi

# Create directory for iptables backup.
if [ ! -d "/etc/iptables" ]; then
  mkdir "/etc/iptables"
  check_errors "Failed to create directory /etc/iptables"
fi


# Create the configuration directory if it does not exist.
if [ ! -d "${CONFIG_DIR}" ]; then
  echo -e "${GREEN}[+] Creating directory ${CONFIG_DIR}.${RESET}"
  mkdir -p "${CONFIG_DIR}"
  check_errors "Failed to create directory ${CONFIG_DIR}"
  
  # Create the configuration file and the servers directory.
  touch "${CONFIG_DIR}/vpnmanager.conf"
  mkdir -p "${CONFIG_DIR}/servers"
  check_errors "Failed to create configuration files"
fi

# Copy all files to the destination directory.
echo -e "${GREEN}[+] Copying files to ${DEST_DIR}.${RESET}"
cp -r ./* "${DEST_DIR}"
check_errors "Failed to copy files to ${DEST_DIR}"

# Set ownership and permissions.
chown -R root:root "${DEST_DIR}"
chmod -R 755 "${DEST_DIR}"

# Copy and install the systemd service file.
echo -e "${GREEN}[+] Installing ${SERVICE_NAME} to systemd.${RESET}"
cp "./service/${SERVICE_NAME}" "/etc/systemd/system/"
check_errors "Failed to copy ${SERVICE_NAME} to systemd directory"

chown root:root "/etc/systemd/system/${SERVICE_NAME}"
chmod 644 "/etc/systemd/system/${SERVICE_NAME}"

# Check if OpenVPN is installed; if not, install it.
if ! command -v openvpn &> /dev/null; then
  echo -e "${YELLOW}[+] OpenVPN is not installed. Installing...${RESET}"
  apt update &> /dev/null
  apt install -y openvpn &> /dev/null
  check_errors "Failed to install OpenVPN"
else
  echo -e "${GREEN}[+] OpenVPN is already installed.${RESET}"
fi

# Reload the systemd daemon.
echo -e "${GREEN}[+] Reloading systemd daemon.${RESET}"
systemctl daemon-reload
check_errors "Failed to reload daemon"

echo -e "${GREEN}[+] Installation complete!${RESET}"
