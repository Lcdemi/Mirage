from dataclasses import dataclass, field
from typing import Optional
import json

@dataclass
class HostsConfig:
    """Configuration for target hosts with IP pattern expansion."""
    range_start: int
    range_end: int

    """Defining Windows host groups"""
    ALL_WINDOWS_CA: list[str] = field(default_factory=list)
    ALL_WINDOWS_DC: list[str] = field(default_factory=list)
    ALL_WINDOWS_ICMP: list[str] = field(default_factory=list)
    ALL_WINDOWS_IIS: list[str] = field(default_factory=list)
    ALL_WINDOWS_FTP: list[str] = field(default_factory=list)
    ALL_WINDOWS_MSSQL: list[str] = field(default_factory=list)
    ALL_WINDOWS_RDP: list[str] = field(default_factory=list)
    ALL_WINDOWS_SMB: list[str] = field(default_factory=list)
    ALL_WINDOWS_SSH: list[str] = field(default_factory=list)
    ALL_WINDOWS_WINRM: list[str] = field(default_factory=list)
    ALL_WINDOWS: list[str] = field(default_factory=list)

    """Defining Linux host groups"""
    ALL_LINUX_APACHE: list[str] = field(default_factory=list)
    ALL_LINUX_DOCKER: list[str] = field(default_factory=list)
    ALL_LINUX_FTP: list[str] = field(default_factory=list)
    ALL_LINUX_ICMP: list[str] = field(default_factory=list)
    ALL_LINUX_MONGO: list[str] = field(default_factory=list)
    ALL_LINUX_MYSQL: list[str] = field(default_factory=list)
    ALL_LINUX_NGINX: list[str] = field(default_factory=list)
    ALL_LINUX_POSTGRESQL: list[str] = field(default_factory=list)
    ALL_LINUX_SAMBA: list[str] = field(default_factory=list)
    ALL_LINUX_SSH: list[str] = field(default_factory=list)
    ALL_LINUX: list[str] = field(default_factory=list)

    """Defining FreeBSD host groups"""
    ALL_ROUTER: list[str] = field(default_factory=list)
    ALL_FREEBSD: list[str] = field(default_factory=list)

    """Defining All Hosts group"""
    ALL_HOSTS: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "HostsConfig":
        """Create HostsConfig from config dictionary."""
        x_range = range(data["range_start"], data["range_end"] + 1)
        windows_patterns = data.get("windows_patterns", {})
        linux_patterns = data.get("linux_patterns", {})
        freebsd_patterns = data.get("freebsd_patterns", {})

        windows_expanded = {}
        # Expand patterns for Windows hosts
        for key, pattern in windows_patterns.items():
            if pattern is not None:
                windows_expanded[key] = [pattern.format(x=x) for x in x_range]
            else:
                windows_expanded[key] = []

        linux_expanded = {}
        # Expand patterns for Linux hosts
        for key, pattern in linux_patterns.items():
            if pattern is not None:
                linux_expanded[key] = [pattern.format(x=x) for x in x_range]
            else:
                linux_expanded[key] = []

        freebsd_expanded = {}
        # Expand patterns for FreeBSD hosts
        for key, pattern in freebsd_patterns.items():
            if pattern is not None:
                freebsd_expanded[key] = [pattern.format(x=x) for x in x_range]
            else:
                freebsd_expanded[key] = []

        # Build ALL_WINDOWS, ALL_LINUX, ALL_FREEBSD by combining respective patterns
        all_windows = [ip for ips in windows_expanded.values() for ip in ips]
        all_linux = [ip for ips in linux_expanded.values() for ip in ips]
        all_freebsd = [ip for ips in freebsd_expanded.values() for ip in ips]

        # Build ALL_HOSTS from all expanded platform lists
        all_hosts = all_windows + all_linux + all_freebsd
        
        return cls(
            # Define Ranges
            range_start=data["range_start"],
            range_end=data["range_end"],

            # Define Windows Hosts
            ALL_WINDOWS_CA=windows_expanded.get("ALL_CA", []),
            ALL_WINDOWS_DC=windows_expanded.get("ALL_DC", []),
            ALL_WINDOWS_ICMP=windows_expanded.get("ALL_ICMP", []),
            ALL_WINDOWS_IIS=windows_expanded.get("ALL_IIS", []),
            ALL_WINDOWS_FTP=windows_expanded.get("ALL_FTP", []),
            ALL_WINDOWS_MSSQL=windows_expanded.get("ALL_MSSQL", []),
            ALL_WINDOWS_RDP=windows_expanded.get("ALL_RDP", []),
            ALL_WINDOWS_SMB=windows_expanded.get("ALL_SMB", []),
            ALL_WINDOWS_SSH=windows_expanded.get("ALL_SSH", []),
            ALL_WINDOWS_WINRM=windows_expanded.get("ALL_WINRM", []),
            ALL_WINDOWS=all_windows,

            # Define Linux Hosts
            ALL_LINUX_APACHE=linux_expanded.get("ALL_APACHE", []),
            ALL_LINUX_DOCKER=linux_expanded.get("ALL_DOCKER", []),
            ALL_LINUX_FTP=linux_expanded.get("ALL_FTP", []),
            ALL_LINUX_ICMP=linux_expanded.get("ALL_ICMP", []),
            ALL_LINUX_MONGO=linux_expanded.get("ALL_MONGO", []),
            ALL_LINUX_MYSQL=linux_expanded.get("ALL_MYSQL", []),
            ALL_LINUX_NGINX=linux_expanded.get("ALL_NGINX", []),
            ALL_LINUX_POSTGRESQL=linux_expanded.get("ALL_POSTGRESQL", []),
            ALL_LINUX_SAMBA=linux_expanded.get("ALL_SAMBA", []),
            ALL_LINUX_SSH=linux_expanded.get("ALL_SSH", []),
            ALL_LINUX=all_linux,

            # Define FreeBSD Hosts
            ALL_ROUTER=freebsd_expanded.get("ALL_ROUTER", []),
            ALL_FREEBSD=all_freebsd,

            # Define All Hosts
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