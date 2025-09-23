import pulumi
import pulumi_digitalocean as digitalocean
from typing import List, Dict
from components.config_types import DropletConfig

class SpokeVMDroplets(pulumi.ComponentResource):
    """
    A Pulumi component that provisions multiple DigitalOcean Droplets
    within existing Spoke VPCs, referencing the VPCs from another stack.
    """

    def __init__(self,
                 name: str,
                 droplet_region: str,
                 droplets: List[DropletConfig],
                 vpc_stack_reference: pulumi.StackReference,
                 opts: pulumi.ResourceOptions = None):
        super().__init__("custom:compute:SpokeVMDroplets", name, {}, opts)

        self.droplet_ids = []
        self.droplet_ips = []

        # Get the outputs from the referenced VPC stack
        # We expect spoke_vpc_ids to be a list of dictionaries, where each dict contains 'id' and 'name'
        # For simplicity, we'll assume spoke_vpc_ids_output is a list of VPC IDs and we'll need to map them to names.
        # A more robust solution would be to export a map from VPC names to IDs from the VPC stack.
        # For this example, we'll assume the VPC stack exports a list of VPC IDs and we'll try to match by name.

        # A more robust way to get VPC IDs by name would be if the VPC stack exported a map like:
        # pulumi.export("spoke_vpcs_map", {"my-spoke-vpc-1": spoke_vpc_1.id, ...})
        # For now, we'll rely on the user to provide correct vpc_name that matches an existing VPC.

        # Let's assume the vpc_stack_reference provides a map of vpc_name to vpc_id
        # If the VPC stack exports a list of IDs, we'd need to iterate and match.
        # For this example, we'll assume the VPC stack exports a dictionary mapping VPC names to their IDs.
        # If the VPC stack only exports a list of IDs, we would need to adjust this logic.

        # For the purpose of this example, let's assume the VPC stack exports a dictionary
        # where keys are VPC names and values are VPC IDs.
        # Example: {"my-spoke-vpc-new": "vpc-id-123", "another-spoke": "vpc-id-456"}
        spoke_vpcs_map = vpc_stack_reference.get_output("spoke_vpcs_map")

        for i, droplet_config in enumerate(droplets):
            # Get the VPC ID for the specified VPC name from the referenced stack's outputs
            # We use apply to handle the Output<Dict> type from StackReference
            vpc_id = spoke_vpcs_map.apply(lambda vpcs: vpcs.get(droplet_config.vpc_name))

            if vpc_id is None:
                pulumi.log.warn(f"VPC with name {droplet_config.vpc_name} not found in referenced VPC stack. Skipping droplet {droplet_config.name}.")
                continue

            droplet = digitalocean.Droplet(
                f"{name}-{droplet_config.name}",
                name=droplet_config.name,
                size=droplet_config.size,
                image=droplet_config.image,
                region=droplet_region,
                vpc_uuid=vpc_id,  # Assign droplet to the specific VPC
                tags=droplet_config.tags,
                opts=pulumi.ResourceOptions(parent=self)
            )
            self.droplet_ids.append(droplet.id)
            self.droplet_ips.append(droplet.ipv4_address)

        # Register outputs
        self.register_outputs({
            "droplet_ids": pulumi.Output.all(*self.droplet_ids),
            "droplet_ips": pulumi.Output.all(*self.droplet_ips),
        })
