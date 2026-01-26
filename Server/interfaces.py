import socket
import InquirerPy.inquirer as inquirer
from InquirerPy.base.control import Choice
from Server.styles import matrix_style

def get_all_local_ips():
    """Get all local IP addresses of the current machine"""
    local_ips = []
    
    try:
        # Get all network interfaces with names
        hostname = socket.gethostname()
        
        # Get all IP addresses associated with the hostname
        all_ips = socket.getaddrinfo(hostname, None)
        for addr_info in all_ips:
            ip = addr_info[4][0]
            if ip not in [ip_info[0] for ip_info in local_ips] and not ip.startswith('127.'):
                local_ips.append((ip, "Hostname Resolution"))
        
        # Also try to get IPs from network interfaces with names (if netifaces available)
        try:
            import netifaces
            interfaces = netifaces.interfaces()
            for interface in interfaces:
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for link in addrs[netifaces.AF_INET]:
                        ip = link['addr']
                        if ip not in [ip_info[0] for ip_info in local_ips] and not ip.startswith('127.'):
                            # Try to get interface description
                            interface_name = interface
                            # Common interface names mapping
                            if interface.startswith('eth'):
                                interface_name = f"Ethernet {interface[3:]}"
                            elif interface.startswith('wlan') or interface.startswith('wlp'):
                                interface_name = f"WiFi {interface[4:]}"
                            elif interface.startswith('en'):
                                interface_name = f"Ethernet {interface[2:]}"
                            elif interface.startswith('tailscale'):
                                interface_name = "Tailscale VPN"
                            elif interface.startswith('tun'):
                                interface_name = f"VPN Tunnel {interface[3:]}"
                            elif interface.startswith('docker'):
                                interface_name = "Docker Network"
                            elif interface == 'lo':
                                interface_name = "Loopback"
                            
                            local_ips.append((ip, interface_name))
        except ImportError:
            pass  # netifaces not available
        
    except:
        pass
    
    # Fallback methods
    try:
        # Try connecting to external service to get outgoing IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            outgoing_ip = s.getsockname()[0]
            if outgoing_ip not in [ip_info[0] for ip_info in local_ips]:
                local_ips.append((outgoing_ip, "Outgoing Connection"))
    except:
        pass
    
    # Add localhost as last resort
    if not local_ips:
        local_ips.append(("127.0.0.1", "Localhost"))
    else:
        # Ensure localhost is included
        if "127.0.0.1" not in [ip_info[0] for ip_info in local_ips]:
            local_ips.append(("127.0.0.1", "Localhost"))
    
    return local_ips

def select_local_ip():
    """Let user select which local IP to use"""
    local_ips = get_all_local_ips()
    
    if not local_ips:
        return "127.0.0.1"
    
    if len(local_ips) == 1:
        return local_ips[0][0]
    
    # Create choices for each IP with interface names
    choices = []
    for ip, interface_name in local_ips:
        # Add description based on IP type
        if ip.startswith('10.') or ip.startswith('192.168.') or (ip.startswith('172.') and 16 <= int(ip.split('.')[1]) <= 31):
            network_type = "Private"
        elif ip.startswith('127.'):
            network_type = "Loopback"
        elif ip.startswith('169.254.'):
            network_type = "Link-local"
        else:
            network_type = "Public"
        
        choices.append(Choice(
            value=ip, 
            name=f"{ip} - {interface_name} ({network_type})"
        ))
    
    # Add exit option
    choices.append(Choice(value=None, name="Exit"))
    
    print("\n=== Network Interface Selection ===")
    selected_ip = inquirer.select(
        message="Select network interface to use:",
        choices=choices,
        style=matrix_style,
        pointer=">>",
        instruction="(Use ↑↓ arrows, Enter to select)",
        default=choices[0].value if choices else None
    ).execute()
    
    if selected_ip is None:
        print("Exiting...")
        exit(0)
    
    return selected_ip