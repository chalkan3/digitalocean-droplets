from dataclasses import dataclass, field
from typing import List, Optional

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
