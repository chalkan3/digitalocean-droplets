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

        self.droplet_ids = []
        self.droplet_ips = []
        self.firewall_ids = []

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
            self.droplet_ids.append(droplet.id)
            self.droplet_ips.append(droplet.ipv4_address)

            # Create Firewall for the Droplet
            if droplet_config.ingress_rules or droplet_config.egress_rules:
                ingress = []
                for rule in droplet_config.ingress_rules:
                    ingress.append(digitalocean.FirewallIngressRuleArgs(
                        protocol=rule.protocol,
                        port_range=rule.port_range,
                        source_addresses=rule.sources.get("addresses"),
                        source_kubernetes_ids=rule.sources.get("kubernetes_ids"),
                        source_load_balancer_uids=rule.sources.get("load_balancer_uids"),
                        source_tags=rule.sources.get("tags"),
                    ))

                egress = []
                for rule in droplet_config.egress_rules:
                    egress.append(digitalocean.FirewallEgressRuleArgs(
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
            "droplet_ids": pulumi.Output.all(*self.droplet_ids),
            "droplet_ips": pulumi.Output.all(*self.droplet_ips),
            "firewall_ids": pulumi.Output.all(*self.firewall_ids),
        })