from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
import re
from Server.pwnboard import fwd_pwnboard

# Callback Global Variables
unprivileged_results = []
privileged_results = []
failed_results = []
error_results = []

SYSTEM_RE = re.compile(r"nt authority\\system", re.IGNORECASE)

console = Console()

def clear_all():
    """Clear all callback results."""
    unprivileged_results.clear()
    privileged_results.clear()
    failed_results.clear()
    error_results.clear()

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

def process_callbacks(results):
    # Reset global lists
    clear_all()

    # Process new callback results
    successful_results = [r for r in results if r["color"] == "#00ff00"]
    for result in successful_results:
        response_text = str(result["response"])
        if SYSTEM_RE.search(response_text):
            fwd_pwnboard(result["target"])
        else:
            unprivileged_results.append(result)
    console.print(f"[bold #00ff00]Forwarded {len(privileged_results)} privileged callbacks to Pwnboard.[/bold #00ff00]")

    failed_results.extend([r for r in results if r["color"] == "#ff0000"])
    error_results.extend([r for r in results if r["color"] == "#ffff00"])