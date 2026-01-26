from pyfiglet import Figlet
from rich.console import Console
from rich.text import Text
from InquirerPy.base.control import Choice
from InquirerPy import inquirer
from rich.columns import Columns
from rich.panel import Panel
from Server.styles import matrix_style, text_style
from Server.config_loader import CONFIG
from Server.discord import fwd_discord

console = Console() # For ASCII Art

def ascii_art(text="MIRAGE", color="bright_green"):
    f = Figlet(font="poison")
    art = f.renderText(text).rstrip('\n')
    console.print(Text(art, style=color))

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
            invalid_ips = [ip for ip in targets if ip not in CONFIG.hosts.ALL_HOSTS]
            
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
        "ALL_HOSTS": CONFIG.hosts.ALL_HOSTS,
        "ALL_DC": CONFIG.hosts.ALL_DC,
        "ALL_IIS": CONFIG.hosts.ALL_IIS,
        "ALL_WINRM": CONFIG.hosts.ALL_WINRM,
        "ALL_ICMP": CONFIG.hosts.ALL_ICMP,
        "ALL_SMB": CONFIG.hosts.ALL_SMB,
    }
    return mapping.get(choice, [])

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
            console.print(f"[#00ff00]✅ Successful:    {success_count} targets[/#00ff00]")
            console.print(f"[#ffff00]⚠️ Warnings:      {warning_count} targets[/#ffff00]")
            console.print(f"[#ff0000]❌ Failed:        {error_count} targets[/#ff0000]")
            console.print(f"[bold white]📋 Total:         {len(sorted_results)} targets[/bold white]")
            console.print(f"[bold white]📈 Success Rate:  {(success_count/len(sorted_results))*100:.2f}%[/bold white]")
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