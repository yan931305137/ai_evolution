import os
import sys
import time
import subprocess
from rich.console import Console

console = Console()
RESTART_CODE = 42

def main():
    """
    OpenClaw Kernel:
    Manages the lifecycle of the AI agent process, handling restarts and crashes.
    """
    console.print("[bold green]OpenClaw Kernel Initialized.[/bold green]")
    console.print("[dim]Starting Supervisor Loop...[/dim]")
    
    restart_count = 0
    
    while True:
        try:
            console.print(f"\n[bold blue]Booting System (Cycle {restart_count + 1})...[/bold blue]")
            
            # Start the CLI/Agent process
            # We use the same python interpreter to run cli.py
            start_time = time.time()
            
            # Set PYTHONPATH to ensure src module can be imported
            env = os.environ.copy()
            if 'PYTHONPATH' not in env:
                env['PYTHONPATH'] = os.getcwd()
            else:
                env['PYTHONPATH'] = os.getcwd() + ':' + env['PYTHONPATH']
            
            process = subprocess.Popen(
                [sys.executable, "src/cli.py"],
                cwd=os.getcwd(),
                env=env # Pass environment with PYTHONPATH
            )
            
            # Wait for process to complete
            return_code = process.wait()
            
            # Calculate uptime
            uptime = time.time() - start_time
            
            if return_code == RESTART_CODE:
                console.print("[bold yellow]System Restart Requested by Agent. Rebooting...[/bold yellow]")
                restart_count += 1
                time.sleep(2) # Give a moment for cleanup/logging
                continue
                
            elif return_code == 0:
                console.print("[bold green]System Shutdown Normally.[/bold green]")
                break
                
            else:
                console.print(f"[bold red]System Crashed (Exit Code: {return_code}).[/bold red]")
                
                # Prevent rapid restart loops if crash happens immediately
                if uptime < 5:
                    console.print("[red]Crash loop detected. Pausing for 10 seconds...[/red]")
                    time.sleep(10)
                else:
                    console.print("[yellow]Restarting in 3 seconds...[/yellow]")
                    time.sleep(3)
                    
                restart_count += 1
                continue
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Kernel Terminated by User.[/yellow]")
            break
        except Exception as e:
            console.print(f"[bold red]Kernel Critical Error: {e}[/bold red]")
            break

if __name__ == "__main__":
    main()
