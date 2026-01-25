from dataclasses import dataclass, field
from typing import Optional
import json

@dataclass
class HostsConfig:
    """Configuration for target hosts with IP pattern expansion."""
    range_start: int
    range_end: int
    ALL_CA: list[str] = field(default_factory=list)
    ALL_DC: list[str] = field(default_factory=list)
    ALL_ICMP: list[str] = field(default_factory=list)
    ALL_IIS: list[str] = field(default_factory=list)
    ALL_FTP: list[str] = field(default_factory=list)
    ALL_MSSQL: list[str] = field(default_factory=list)
    ALL_RDP: list[str] = field(default_factory=list)
    ALL_SMB: list[str] = field(default_factory=list)
    ALL_SSH: list[str] = field(default_factory=list)
    ALL_WINRM: list[str] = field(default_factory=list)
    ALL_HOSTS: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "HostsConfig":
        """Create HostsConfig from config dictionary."""
        x_range = range(data["range_start"], data["range_end"] + 1)
        patterns = data.get("patterns", {})
        
        expanded = {}
        for key, pattern in patterns.items():
            if pattern is not None:
                expanded[key] = [pattern.format(x=x) for x in x_range]
            else:
                expanded[key] = []
        
        # Build ALL_HOSTS from all non-empty host lists
        all_hosts = [ip for ips in expanded.values() for ip in ips]
        
        return cls(
            range_start=data["range_start"],
            range_end=data["range_end"],
            ALL_CA=expanded.get("ALL_CA", []),
            ALL_DC=expanded.get("ALL_DC", []),
            ALL_ICMP=expanded.get("ALL_ICMP", []),
            ALL_IIS=expanded.get("ALL_IIS", []),
            ALL_FTP=expanded.get("ALL_FTP", []),
            ALL_MSSQL=expanded.get("ALL_MSSQL", []),
            ALL_RDP=expanded.get("ALL_RDP", []),
            ALL_SMB=expanded.get("ALL_SMB", []),
            ALL_SSH=expanded.get("ALL_SSH", []),
            ALL_WINRM=expanded.get("ALL_WINRM", []),
            ALL_HOSTS=all_hosts
        )

@dataclass
class LoggingConfig:
    """Configuration for logging and notifications."""
    PWNBOARD_URL: Optional[str] = None
    PWNBOARD_AUTH_TOKEN: Optional[str] = None
    DISCORD_WEBHOOK_URL: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "LoggingConfig":
        """Create LoggingConfig from config dictionary."""
        return cls(
            PWNBOARD_URL=data.get("PWNBOARD_URL"),
            PWNBOARD_AUTH_TOKEN=data.get("PWNBOARD_AUTH_TOKEN"),
            DISCORD_WEBHOOK_URL=data.get("DISCORD_WEBHOOK_URL")
        )

@dataclass
class OtherConfig:
    """Configuration for server and execution settings."""
    PORT: int = 8080
    TIMEOUT: int = 30
    CONCURRENCY: int = 8
    THROTTLE_MS: int = 50
    TIMEZONE: str = "EST"

    @classmethod
    def from_dict(cls, data: dict) -> "OtherConfig":
        """Create OtherConfig from config dictionary."""
        return cls(
            PORT=data.get("PORT", 8080),
            TIMEOUT=data.get("TIMEOUT", 30),
            CONCURRENCY=data.get("CONCURRENCY", 8),
            THROTTLE_MS=data.get("THROTTLE_MS", 50),
            TIMEZONE=data.get("TIMEZONE", "EST")
        )

@dataclass
class MirageConfig:
    """Main configuration class combining all config sections."""
    hosts: HostsConfig
    logging: LoggingConfig
    other: OtherConfig

    @classmethod
    def load(cls, file_path: str = "Server/config.json") -> "MirageConfig":
        """Load and parse configuration from JSON file."""
        with open(file_path, "r") as f:
            data = json.load(f)
        
        return cls(
            hosts=HostsConfig.from_dict(data["hosts"]),
            logging=LoggingConfig.from_dict(data["logging"]),
            other=OtherConfig.from_dict(data["other"])
        )