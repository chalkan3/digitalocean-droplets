#!/bin/bash
set -ex

exec > /tmp/bootstrap.log 2>&1

echo "--- Bootstrap script started at $(date) ---"

# Update apt-get
apt-get update -y

echo "--- apt-get update finished ---"

# Install dependencies
apt-get install -y curl

echo "--- curl installed ---"

# Download FRP
FRP_VERSION="0.51.3" # You can change this to the desired version
ARCH=$(dpkg --print-architecture)

case "$ARCH" in
  "amd64")
    FRP_ARCH="linux_amd64"
    ;;
  "arm64")
    FRP_ARCH="linux_arm64"
    ;;
  *)
    echo "Unsupported architecture: $ARCH"
    exit 1
    ;;
esac

FRP_TARBALL="frp_${FRP_VERSION}_${FRP_ARCH}.tar.gz"
FRP_URL="https://github.com/fatedier/frp/releases/download/v${FRP_VERSION}/${FRP_TARBALL}"

echo "Downloading FRP from: $FRP_URL"
wget -q "$FRP_URL" -O "/tmp/$FRP_TARBALL"

echo "--- FRP downloaded ---"

# Create FRP configuration directory
mkdir -p /etc/frp

tar -xzf "/tmp/$FRP_TARBALL" -C /tmp
mv "/tmp/frp_${FRP_VERSION}_${FRP_ARCH}/frps" /usr/local/bin/frps
# No need to move frps.ini, we'll create frps.toml

echo "--- FRP extracted ---"

# Create frps.toml
cat <<EOF > /etc/frp/frps.toml
[common]
bindPort = 7000
vhostHTTPPort = 80
vhostHTTPSPort = 443
dashboardPort = 7500
dashboardUser = "admin"
dashboardPwd = "password" # Consider changing this to a more secure password
logFile = "/var/log/frps.log"
logLevel = "info"
logMaxDays = 3
authentication_method = "none" # Explicitly disable token
EOF

echo "--- frps.toml created ---"

# Create systemd service file
cat <<EOF > /etc/systemd/system/frps.service
[Unit]
Description=Frp Server Service
After=network.target

[Service]
Type=simple
User=nobody
Restart=on-failure
RestartSec=5s
ExecStart=/usr/local/bin/frps -c /etc/frp/frps.toml # Changed to frps.toml
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF

echo "--- frps.service created ---"

# Enable and start the service
systemctl enable frps
systemctl start frps

echo "--- frps service started ---"

echo "--- Bootstrap script finished at $(date) ---"