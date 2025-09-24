import unittest
from unittest.mock import patch, MagicMock
import pulumi
from pulumi import Output
from pulumi_digitalocean import Provider, SshKey, Droplet, Volume, VolumeAttachment, Firewall, FirewallInboundRuleArgs, FirewallOutboundRuleArgs
from components.spoke_vm_droplets import SpokeVMDroplets
from components.config_types import DropletConfig, SaltGrainsConfig, IngressRule, EgressRule
import yaml

# Mock the Pulumi outputs and resources
class Mocks(pulumi.runtime.Mocks):
    def __init__(self):
        self.resources = [] # Initialize resources list
        super().__init__()

    def call(self, token, args, provider):
        if token == "digitalocean:index/getVpc:getVpc":
            return {"id": "mock-vpc-id"}
        if token == "digitalocean:index/getVolume:getVolume":
            return {"id": "mock-volume-id"}
        return {}

    def new_resource(self, args: pulumi.runtime.MockResourceArgs): # Corrected type hint
        # Generate a mock ID for the resource
        mock_id = f"mock-{args.name}-{len(self.resources) + 1}" # More predictable ID

        state = {}
        if args.typ == "digitalocean:index/droplet:Droplet":
            state = {"ipv4_address": f"192.0.2.{len(self.resources) + 1}"}
        elif args.typ == "digitalocean:index/volume:Volume":
            state = {"name": f"mock-volume-name-{len(self.resources) + 1}"}
        elif args.typ == "digitalocean:index/firewall:Firewall":
            pass # No specific state needed for firewall mock
        elif args.typ == "digitalocean:index/sshKey:SshKey":
            state = {"fingerprint": f"mock-ssh-fingerprint-{len(self.resources) + 1}"}

        self.resources.append({"token": args.typ, "name": args.name, "inputs": args.inputs, "provider": args.provider, "id": mock_id, "state": state})
        return mock_id, state

pulumi.runtime.set_mocks(Mocks())

class TestSpokeVMDroplets(unittest.TestCase):

    @pulumi.runtime.test
    def test_droplet_creation(self):
        # Mock StackReference output
        mock_vpc_stack_ref = MagicMock()
        mock_vpc_stack_ref.get_output.return_value = Output.from_input({"production-spoke": "mock-vpc-id"})

        # Define a sample DropletConfig
        droplet_config = DropletConfig(
            name="test-droplet",
            size="s-1vcpu-1gb",
            image="ubuntu-22-04-x64",
            vpc_name="production-spoke",
            tags=["test", "pulumi"],
            salt_enabled=False,
            droplet_bootstrap_script="echo 'hello'",
            volume_size_gb=10,
            ingress_rules=[
                IngressRule(protocol="tcp", port_range="22", sources={"addresses": ["0.0.0.0/0"]})
            ],
            egress_rules=[
                EgressRule(protocol="tcp", port_range="all", destinations={"addresses": ["0.0.0.0/0"]})
            ]
        )

        # Instantiate the component
        spoke_vm_droplets = SpokeVMDroplets(
            "test-spoke-vm-droplets",
            droplet_region="nyc3",
            droplets=[droplet_config],
            vpc_stack_reference=mock_vpc_stack_ref,
        )

        # Assert on the outputs
        self.assertIsNotNone(spoke_vm_droplets.droplet_ips)
        self.assertIsNotNone(spoke_vm_droplets.volume_device_paths)
        self.assertIsNotNone(spoke_vm_droplets.firewall_ids)

        # Check specific values (requires resolving outputs)
        def check_ips(ips):
            self.assertEqual(len(ips), 1)
            self.assertTrue(ips[0].startswith("192.0.2."))
        Output.all(*spoke_vm_droplets.droplet_ips).apply(check_ips)

        def check_volume_paths(paths):
            self.assertEqual(len(paths), 1)
            self.assertTrue(paths[0].startswith("/dev/disk/by-id/scsi-0DO_Volume_mock-volume-name-"))
        Output.all(*spoke_vm_droplets.volume_device_paths).apply(check_volume_paths)

        def check_firewall_ids(ids):
            self.assertEqual(len(ids), 1)
            self.assertTrue(ids[0].startswith("mock-")) # Corrected assertion
        Output.all(*spoke_vm_droplets.firewall_ids).apply(check_firewall_ids)

if __name__ == '__main__':
    unittest.main()