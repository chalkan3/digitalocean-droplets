# 🚀 DigitalOcean Droplets Project

## ✨ Project Overview

This Pulumi project in Python provisions multiple virtual machines (Droplets) on DigitalOcean, placing them within the existing Spoke VPCs created by a complementary Pulumi project (the Hub-Spoke VPC project). It demonstrates the use of `pulumi.StackReference` to access outputs from other stacks, ensuring a modular and interconnected architecture.

## ✨ New Features: Conditional Bootstrap and Firewall Management

This project has been extended to provide conditional Droplet bootstrapping and comprehensive firewall management using DigitalOcean Firewalls.

### Conditional Bootstrap Logic

Droplets can now be provisioned with one of two bootstrap mechanisms, controlled by the `salt-enabled` configuration variable:

*   **SaltStack Bootstrap (`salt-enabled: true`)**: If `salt-enabled` is set to `true`, the Droplet will be provisioned with a `user_data` script that installs and configures the SaltStack minion. This requires `salt-master-ip` to be specified, and optionally `salt-grains` for custom minion grains.
*   **Custom Bootstrap Script (`salt-enabled: false`)**: If `salt-enabled` is `false`, the Droplet will use a custom `user_data` script provided via the `droplet-bootstrap-script` configuration variable. This allows for flexible provisioning without SaltStack.

### Firewall Management

Each Droplet can now have a dedicated DigitalOcean Firewall associated with it, configured via `ingress-rules` and `egress-rules`.

*   **`ingress-rules`**: A list of inbound rules, where each rule specifies `protocol`, `port-range`, and `sources` (e.g., `addresses`, `kubernetes_ids`, `load_balancer_uids`, `tags`).
*   **`egress-rules`**: A list of outbound rules, where each rule specifies `protocol`, `port-range`, and `destinations` (e.g., `addresses`, `kubernetes_ids`, `load_balancer_uids`, `tags`).

### New Configuration Variables

The following new variables are available within each Droplet's configuration block in `Pulumi.stack.yaml`:

*   `salt-enabled` (boolean, optional, default: `false`): Set to `true` to enable SaltStack bootstrap for the Droplet.
*   `salt-master-ip` (string, optional): The IP address of the Salt Master. Required if `salt-enabled` is `true`.
*   `salt-grains` (object, optional): A dictionary of custom Salt grains for the minion. Contains `roles` (list of strings) and `environment` (string).
*   `droplet-bootstrap-script` (string, optional): A multi-line string containing the bash script to be executed as `user_data` if `salt-enabled` is `false`.
*   `ingress-rules` (list of objects, optional): Defines inbound firewall rules for the Droplet.
    *   `protocol` (string): The network protocol (e.g., `tcp`, `udp`, `icmp`, `all`).
    *   `port-range` (string): The port or port range (e.g., `22`, `80-90`, `all`).
    *   `sources` (object): Specifies allowed sources. Can contain `addresses` (list of CIDR blocks), `kubernetes_ids` (list of Kubernetes cluster IDs), `load_balancer_uids` (list of Load Balancer UIDs), or `tags` (list of Droplet tags).
*   `egress-rules` (list of objects, optional): Defines outbound firewall rules for the Droplet.
    *   `protocol` (string): The network protocol.
    *   `port-range` (string): The port or port range.
    *   `destinations` (object): Specifies allowed destinations. Can contain `addresses` (list of CIDR blocks), `kubernetes_ids` (list of Kubernetes cluster IDs), `load_balancer_uids` (list of Load Balancer UIDs), or `tags` (list of Droplet tags).



Before you begin, ensure you have the following installed and configured:

*   **Pulumi CLI**: [Pulumi Installation Guide](https://www.pulumi.com/docs/get-started/install/)
*   **DigitalOcean Account**: An active DigitalOcean account.
*   **DigitalOcean API Token**: An API token with read and write permissions to manage VPCs and Droplets.
*   **Python 3.x**: [Python Installation Guide](https://www.python.org/downloads/)
*   **`gh cli`**: For creating GitHub repositories (optional, but used in this example).
*   **Deployed Hub-Spoke VPC Project**: This project depends on the outputs of a deployed stack from the `digitalocean-hub-spoke-vpc` project. Ensure the referenced stack is active and exporting `spoke_vpcs_map`.

## 📂 Project Structure

```
.
├── __main__.py
├── Pulumi.yaml
├── Pulumi.dev.yaml
├── requirements.txt
└── components/
    ├── __init__.py
    ├── config_types.py
    └── spoke_vm_droplets.py
```

*   `__main__.py`: The main Pulumi program that orchestrates Droplet creation.
*   `Pulumi.yaml`: The Pulumi project configuration file.
*   `Pulumi.dev.yaml`: An example stack configuration file for the development environment.
*   `requirements.txt`: Lists the project's Python dependencies.
*   `components/`: Contains the `SpokeVMDroplets` Pulumi component to modularize Droplet creation logic.
    *   `config_types.py`: Defines dataclasses for Droplet and related configurations (SaltStack, Firewall).
    *   `salt_bootstrap.py`: Contains logic for generating SaltStack bootstrap scripts.
    *   `spoke_vm_droplets.py`: Implements the `SpokeVMDroplets` component, including conditional bootstrap and firewall management.

## 🛠️ Setup and Deployment

Follow the steps below to set up and deploy your Droplets.

### 1. Clone the Repository

```bash
git clone https://github.com/chalkan3/digitalocean-droplets.git
cd digitalocean-droplets
```

### 2. Configure Python Environment

Create and activate a Python virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

Install the necessary Python dependencies:

```bash
pip install -r requirements.txt
```

### 4. Install Pulumi DigitalOcean Provider

Ensure the Pulumi DigitalOcean provider is installed:

```bash
pulumi plugin install resource digitalocean 4.53.0
```

### 5. Initialize Pulumi Stack

Create a new Pulumi stack (e.g., `dev`):

```bash
pulumi stack init dev
```

### 6. Configure DigitalOcean Token

Set your DigitalOcean API token. **This token will be securely stored by Pulumi.**

```bash
pulumi config set digitalocean:token --secret dop_v1_YOUR_TOKEN_HERE
```
*(Replace `dop_v1_YOUR_TOKEN_HERE` with your actual DigitalOcean token.)*

### 7. Configure Project Variables

Define the configuration variables for your stack. Variable names follow the `kebab-case` standard.

```bash
pulumi config set digitalocean-droplets:vpc-stack-name chalkan3/digitalocean-hub-spoke-vpc/test
pulumi config set digitalocean-droplets:droplet-region nyc3
pulumi config set digitalocean-droplets:droplets --secret 'YOUR_YAML_CONFIG_HERE'

**Note**: Due to the complexity of the `droplets` configuration with conditional bootstrap and firewall rules, it is highly recommended to manage this configuration directly in your `Pulumi.<stack-name>.yaml` file (e.g., `Pulumi.dev.yaml`) rather than via `pulumi config set` commands. Refer to the example `Pulumi.dev.yaml` below for a comprehensive illustration.
```

#### Example `Pulumi.dev.yaml`

Here's a comprehensive example of how your `Pulumi.dev.yaml` file should look with the new configuration options:

```yaml
config:
  digitalocean:region: nyc3
  digitalocean-droplets:vpc-stack-name: organization/digitalocean-hub-spoke-vpc/dev # Replace with your VPC stack reference
  digitalocean-droplets:droplet-region: nyc3
  digitalocean-droplets:droplets: |
    - name: salt-minion-droplet
      size: s-1vcpu-1gb
      image: ubuntu-22-04-x64
      vpc-name: spoke-vpc-1 # Ensure this matches a VPC name in your referenced VPC stack
      tags:
        - salt-minion
        - dev
      salt-enabled: true
      salt-master-ip: 192.0.2.10 # Replace with your Salt Master IP
      salt-grains:
        roles:
          - web-server
        environment: development
      ingress-rules:
        - protocol: tcp
          port-range: "22"
          sources:
            addresses:
              - 0.0.0.0/0
        - protocol: tcp
          port-range: "80"
          sources:
            addresses:
              - 0.0.0.0/0
      egress-rules:
        - protocol: tcp
          port-range: "all"
          destinations:
            addresses:
              - 0.0.0.0/0
    - name: plain-droplet
      size: s-1vcpu-1gb
      image: ubuntu-22-04-x64
      vpc-name: spoke-vpc-2 # Ensure this matches a VPC name in your referenced VPC stack
      tags:
        - plain-vm
        - dev
      salt-enabled: false
      droplet-bootstrap-script: |
        #!/bin/bash
        echo "Hello from a plain droplet!" > /tmp/hello.txt
        apt-get update -y
        apt-get install -y nginx
        systemctl start nginx
      ingress-rules:
        - protocol: tcp
          port-range: "22"
          sources:
            addresses:
              - 0.0.0.0/0
        - protocol: tcp
          port-range: "80"
          sources:
            addresses:
              - 0.0.0.0/0
      egress-rules:
        - protocol: tcp
          port-range: "all"
          destinations:
            addresses:
              - 0.0.0.0/0
encryptionsalt: v1:YOUR_SALT_HERE=:v1:YOUR_SALT_HERE:YOUR_SALT_HERE==
```
*(The `encryptionsalt` and secure token are automatically generated by Pulumi.)*

### 8. Deploy the Stack

Run the `pulumi up` command to provision the resources on DigitalOcean. The `--yes` flag automatically confirms the deployment.

```bash
PULUMI_PYTHON_CMD=./venv/bin/python pulumi up --stack dev --yes
```

## 📊 Deployment Outputs

After successful deployment, Pulumi will display the following outputs:

*   `droplet_ids`: A list of the created Droplet IDs.
*   `droplet_ips`: A list of the created Droplet IPv4 addresses.
*   `firewall_ids`: A list of the created Firewall IDs.

## 🗑️ Destroy Resources

To destroy all resources provisioned by this stack:

```bash
PULUMI_PYTHON_CMD=./venv/bin/python pulumi destroy --stack dev --yes
```

## ❌ Remove Stack Completely

To completely remove the Pulumi stack and all its history and configuration (including sensitive data like tokens), run:

```bash
pulumi stack rm dev --yes
```

## 💡 Important Notes

*   This project depends on the existence of a deployed stack from the `digitalocean-hub-spoke-vpc` project. Ensure the referenced stack is active and exporting `spoke_vpcs_map`.
*   The `vpc-stack-name` should be in the format `org_name/project_name/stack_name` (e.g., `chalkan3/digitalocean-hub-spoke-vpc/test`).

```