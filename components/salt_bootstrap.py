import yaml
from typing import Optional
from .config_types import SaltGrainsConfig

def generate_salt_bootstrap_script(
    droplet_name: str,
    salt_master_ip: str,
    salt_grains: Optional[SaltGrainsConfig] = None
) -> str:
    """
    Generates a user data script for bootstrapping a Salt minion on a DigitalOcean Droplet.
    """

    grains_yaml_content = ""
    if salt_grains:
        grains_block = {"grains": salt_grains.__dict__}
        grains_yaml_content = yaml.dump(grains_block, indent=2)

    user_data = f"""#!/bin/bash
# Log all output for easier debugging
exec > >(tee /var/log/cloud-init-output.log|logger -t user-data -s 2>/dev/console) 2>&1
set -x

echo "--- User data script started at $(date) ---"

# Wait for network to be fully ready (DigitalOcean specific check might be needed, but general wait is fine)
# For DigitalOcean, network is usually ready quickly, but a small delay can help.
sleep 10
echo "--- Network is ready ---"

# Update and install dependencies
apt-get update -y
apt-get install -y curl

cd /tmp

echo "--- Downloading Salt bootstrap script ---"
curl -o bootstrap-salt.sh -L https://raw.githubusercontent.com/saltstack/salt-bootstrap/stable/bootstrap-salt.sh
if [ ! -f "bootstrap-salt.sh" ]; then
    echo "!!! FAILED to download bootstrap-salt.sh"
    exit 1
fi

echo "--- Running Salt bootstrap script ---"
chmod +x bootstrap-salt.sh
sh ./bootstrap-salt.sh -A {salt_master_ip} -i {droplet_name}

# Append grains if provided
if [ -n "{grains_yaml_content}" ]; then
    echo "--- Appending grains to /etc/salt/minion.d/99-pulumi-grains.conf ---"
    mkdir -p /etc/salt/minion.d
    cat << EOF > /etc/salt/minion.d/99-pulumi-grains.conf
{grains_yaml_content}
EOF
fi

echo "--- Restarting Salt minion ---"
systemctl restart salt-minion

echo "--- Waiting for salt-minion to become active (max 60 seconds) ---"
for i in {{1..12}}; do
    if systemctl is-active --quiet salt-minion; then
        echo ">>> Salt minion is active!"
        break
    fi
    echo "Waiting for salt-minion... attempt $i/12"
    sleep 5
done

echo "--- FINAL DIAGNOSTICS ---"
echo ">>> Checking salt-minion service status:"
systemctl status salt-minion --no-pager || echo "salt-minion service status check failed"

echo ">>> Verifying grains with salt-call:"
salt-call grains.items --local || echo "salt-call command failed"

echo "--- User data script finished at $(date) ---"
"""
    return user_data
