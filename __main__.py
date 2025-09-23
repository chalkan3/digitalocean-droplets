import pulumi
from pulumi import Config
import yaml
from components.spoke_vm_droplets import SpokeVMDroplets
from components.config_types import DropletConfig

# Load configuration
config = Config()

vpc_stack_name = config.require("vpc-stack-name")
droplet_region = config.require("droplet-region")

droplets_yaml = config.require("droplets")
droplets_config_raw = yaml.safe_load(droplets_yaml)

droplets = []
for droplet_raw in droplets_config_raw:
    # Manually map kebab-case to snake_case for dataclass
    droplet_processed = {
        "name": droplet_raw["name"],
        "size": droplet_raw["size"],
        "image": droplet_raw["image"],
        "vpc_name": droplet_raw["vpc-name"], # Map vpc-name to vpc_name
        "tags": droplet_raw.get("tags", [])
    }
    droplets.append(DropletConfig(**droplet_processed))

# Create a StackReference to the VPC Hub-Spoke project
vpc_stack_ref = pulumi.StackReference(vpc_stack_name)

# Get the outputs from the VPC stack
hub_vpc_id = vpc_stack_ref.get_output("hub_vpc_id")
spoke_vpc_ids_output = vpc_stack_ref.get_output("spoke_vpc_ids")

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
