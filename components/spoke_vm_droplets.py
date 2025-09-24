import pulumi
import pulumi_digitalocean as digitalocean
from typing import List, Dict
from components.config_types import DropletConfig, IngressRule, EgressRule, SaltGrainsConfig
from components.salt_bootstrap import generate_salt_bootstrap_script

class SpokeVMDroplets(pulumi.ComponentResource):
    """
    A Pulumi component that provisions multiple DigitalOcean Droplets
    within existing Spoke VPCs, referencing the VPCs from another stack,
    with conditional bootstrap and firewall management.
    """

    def __init__(self,
                 name: str,
                 droplet_region: str,
                 droplets: List[DropletConfig],
                 vpc_stack_reference: pulumi.StackReference,
                 opts: pulumi.ResourceOptions = None):
        super().__init__("custom:compute:SpokeVMDroplets", name, {}, opts)

        self.droplet_ips = []
        self.firewall_ids = []
        self.volume_ids = []
        self.volume_device_paths = []

        spoke_vpcs_map = vpc_stack_reference.get_output("spoke_vpcs_map")

        for i, droplet_config in enumerate(droplets):
            vpc_id = spoke_vpcs_map.apply(lambda vpcs: vpcs.get(droplet_config.vpc_name))

            if vpc_id is None:
                pulumi.log.warn(f"VPC with name {droplet_config.vpc_name} not found in referenced VPC stack. Skipping droplet {droplet_config.name}.")
                continue

            user_data_script = None
            if droplet_config.salt_enabled:
                if not droplet_config.salt_master_ip:
                    pulumi.log.error(f"Salt master IP is required for Salt-enabled droplet {droplet_config.name}")
                    continue
                user_data_script = generate_salt_bootstrap_script(
                    droplet_name=droplet_config.name,
                    salt_master_ip=droplet_config.salt_master_ip,
                    salt_grains=droplet_config.salt_grains
                )
            elif droplet_config.droplet_bootstrap_script:
                user_data_script = droplet_config.droplet_bootstrap_script

            droplet = digitalocean.Droplet(
                f"{name}-{droplet_config.name}",
                name=droplet_config.name,
                size=droplet_config.size,
                image=droplet_config.image,
                region=droplet_region,
                vpc_uuid=vpc_id,
                tags=droplet_config.tags,
                user_data=user_data_script,
                opts=pulumi.ResourceOptions(parent=self)
            )
            self.droplet_ips.append(droplet.ipv4_address)

            # Create Volume and attach it if volume_size_gb is specified
            if droplet_config.volume_size_gb:
                pulumi.log.info(f"Creating volume for {droplet_config.name} with size {droplet_config.volume_size_gb}GB") # Add this line
                volume = digitalocean.Volume(
                    f"{name}-{droplet_config.name}-volume",
                    region=droplet_region,
                    size=droplet_config.volume_size_gb,
                    initial_filesystem_type="ext4", # Default filesystem type
                    description=f"Volume for {droplet_config.name}",
                    opts=pulumi.ResourceOptions(parent=droplet)
                )
                digitalocean.VolumeAttachment(
                    f"{name}-{droplet_config.name}-volume-attachment",
                    droplet_id=droplet.id,
                    volume_id=volume.id,
                    opts=pulumi.ResourceOptions(parent=volume)
                )
                self.volume_ids.append(volume.id)
                self.volume_device_paths.append(pulumi.Output.concat("/dev/disk/by-id/scsi-0DO_Volume_", volume.name))


            # Create Firewall for the Droplet
            if droplet_config.ingress_rules or droplet_config.egress_rules:
                ingress = []
                for rule in droplet_config.ingress_rules:
                    ingress.append(digitalocean.FirewallInboundRuleArgs(
                        protocol=rule.protocol,
                        port_range=rule.port_range,
                        source_addresses=rule.sources.get("addresses"),
                        source_kubernetes_ids=rule.sources.get("kubernetes_ids"),
                        source_load_balancer_uids=rule.sources.get("load_balancer_uids"),
                        source_tags=rule.sources.get("tags"),
                    ))

                egress = []
                for rule in droplet_config.egress_rules:
                    egress.append(digitalocean.FirewallOutboundRuleArgs(
                        protocol=rule.protocol,
                        port_range=rule.port_range,
                        destination_addresses=rule.destinations.get("addresses"),
                        destination_kubernetes_ids=rule.destinations.get("kubernetes_ids"),
                        destination_load_balancer_uids=rule.destinations.get("load_balancer_uids"),
                        destination_tags=rule.destinations.get("tags"),
                    ))

                firewall = digitalocean.Firewall(
                    f"{name}-{droplet_config.name}-firewall",
                    name=f"{droplet_config.name}-firewall",
                    droplet_ids=[droplet.id],
                    inbound_rules=ingress,
                    outbound_rules=egress,
                    opts=pulumi.ResourceOptions(parent=droplet)
                )
                self.firewall_ids.append(firewall.id)

        # Register outputs
        self.register_outputs({
            "droplet_ips": pulumi.Output.all(*self.droplet_ips),
            "firewall_ids": pulumi.Output.all(*self.firewall_ids),
            "volume_ids": pulumi.Output.all(*self.volume_ids),
            "volume_device_paths": pulumi.Output.all(*self.volume_device_paths),
        })