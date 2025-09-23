import pulumi
from pulumi import Config
import yaml
from components.spoke_vm_droplets import SpokeVMDroplets
from components.config_types import DropletConfig, SaltGrainsConfig, IngressRule, EgressRule
from typing import List, Dict, Any

def kebab_to_snake(d: Any) -> Any:
    if isinstance(d, dict):
        return {
            key.replace('-', '_'): kebab_to_snake(value)
            for key, value in d.items()
        }
    if isinstance(d, list):
        return [kebab_to_snake(item) for item in d]
    return d

# Load configuration
config = Config()

vpc_stack_name = config.require("vpc-stack-name")
droplet_region = config.require("droplet-region")

droplets_yaml = config.require("droplets")
droplets_config_raw = yaml.safe_load(droplets_yaml)

droplets: List[DropletConfig] = []
for droplet_raw in droplets_config_raw:
    # Convert raw config to snake_case
    droplet_processed = kebab_to_snake(droplet_raw)

    # Extract and process nested configurations
    salt_grains_config = None
    if "salt_grains" in droplet_processed and droplet_processed["salt_grains"] is not None:
        salt_grains_config = SaltGrainsConfig(**droplet_processed["salt_grains"])

    ingress_rules_config = []
    if "ingress_rules" in droplet_processed and droplet_processed["ingress_rules"] is not None:
        ingress_rules_config = [IngressRule(**rule) for rule in droplet_processed["ingress_rules"]]

    egress_rules_config = []
    if "egress_rules" in droplet_processed and droplet_processed["egress_rules"] is not None:
        egress_rules_config = [EgressRule(**rule) for rule in droplet_processed["egress_rules"]]

    droplets.append(DropletConfig(
        name=droplet_processed["name"],
        size=droplet_processed["size"],
        image=droplet_processed["image"],
        vpc_name=droplet_processed["vpc_name"],
        tags=droplet_processed.get("tags", []),
        salt_enabled=droplet_processed.get("salt_enabled", False),
        salt_master_ip=droplet_processed.get("salt_master_ip"),
        salt_grains=salt_grains_config,
        droplet_bootstrap_script=droplet_processed.get("droplet_bootstrap_script"),
        ingress_rules=ingress_rules_config,
        egress_rules=egress_rules_config,
    ))

# Create a StackReference to the VPC Hub-Spoke project
vpc_stack_ref = pulumi.StackReference(vpc_stack_name)

# Instantiate the SpokeVMDroplets component
spoke_vm_droplets = SpokeVMDroplets(
    "spoke-vm-droplets",
    droplet_region=droplet_region,
    droplets=droplets,
    vpc_stack_reference=vpc_stack_ref
)

# Export outputs
pulumi.export("droplet_ids", spoke_vm_droplets.droplet_ids)
pulumi.export("droplet_ips", spoke_vm_droplets.droplet_ips)
pulumi.export("firewall_ids", spoke_vm_droplets.firewall_ids)