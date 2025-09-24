#!/bin/bash

# Check if a key name argument is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <key_name>"
  echo "Example: $0 my_droplet_key"
  exit 1
fi

KEY_NAME="$1"

# Define the base directory for SSH keys
SSH_BASE_DIR="$HOME/.ssh/digitalocean/droplet"

# Create the directory if it doesn't exist
mkdir -p "$SSH_BASE_DIR"

# Navigate to the Pulumi project directory
# Ensure you are in the digitalocean-droplets directory before running this script
cd /Users/chalkan3/.projects/digitalocean-droplets || { echo "Error: Could not navigate to the Pulumi project directory."; exit 1; }

# Get the private key from Pulumi stack output
# The 'pulumi stack output' command should be run in the Pulumi project directory
PRIVATE_KEY=$(PULUMI_PYTHON_CMD=./venv/bin/python pulumi stack output private_key_pem --stack frps-proxy-production --show-secrets)

# Check if the key was retrieved successfully
if [ -z "$PRIVATE_KEY" ]; then
  echo "Error: Could not retrieve the private key from Pulumi output. Ensure the 'frps-proxy-production' stack is active and the 'private_key_pem' key exists."
  exit 1
}

# Save the private key to a file
KEY_PATH="$SSH_BASE_DIR/$KEY_NAME"
echo "$PRIVATE_KEY" > "$KEY_PATH"

# Set appropriate permissions for the private key
chmod 600 "$KEY_PATH"

echo "Private key saved to: $KEY_PATH"
echo "You can now use it to SSH into the droplet. Example: ssh -i $KEY_PATH root@<droplet_ip>"