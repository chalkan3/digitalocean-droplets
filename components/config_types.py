from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class SaltGrainsConfig:
    """
    Configuration for SaltStack grains.
    """
    roles: List[str] = field(default_factory=list)
    environment: Optional[str] = None
    host_image: Optional[str] = None
    vpc_name: Optional[str] = None
    managed_by: Optional[str] = None
    machine_size: Optional[str] = None
    datacenter: Optional[str] = None
    datacenter_region: Optional[str] = None

@dataclass
class SaltConfig:
    """
    Configuration for SaltStack minion.
    """
    master_ip: str
    grains: SaltGrainsConfig

@dataclass
class IngressRule:
    """
    Configuration for a DigitalOcean Firewall Ingress Rule.
    """
    protocol: str
    port_range: str
    sources: Dict[str, List[str]] = field(default_factory=dict)

@dataclass
class EgressRule:
    """
    Configuration for a DigitalOcean Firewall Egress Rule.
    """
    protocol: str
    port_range: str
    destinations: Dict[str, List[str]] = field(default_factory=dict)

@dataclass
class DropletConfig:
    """
    Configuration for a DigitalOcean Droplet.
    """
    name: str
    size: str
    image: str
    vpc_name: str
    tags: Optional[List[str]] = field(default_factory=list)
    salt_enabled: Optional[bool] = False
    salt_master_ip: Optional[str] = None
    salt_grains: Optional[SaltGrainsConfig] = None
    droplet_bootstrap_script: Optional[str] = None
    volume_size_gb: Optional[int] = None
    ingress_rules: Optional[List[IngressRule]] = field(default_factory=list)
    egress_rules: Optional[List[EgressRule]] = field(default_factory=list)