
import time
import random
import threading
import sys
import psutil
from datetime import datetime
from typing import Optional, Dict, List

from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.table import Table
from rich.text import Text
from rich.console import Console
from rich.align import Align

class AgentMonitor:
    """
    Real-time CLI Dashboard for monitoring Agent internals.
    Displays:
    - System Stats (CPU/Memory)
    - Agent State (Thinking/Acting/Idle)
    - Needs (Energy/Health/Social)
    - Activity Log
    """
    
    def __init__(self):
        self.console = Console()
        self.layout = Layout()
        self.running = False
        self.thread = None
        
        # Internal State
        self.agent_state = "IDLE"
        self.current_task = "Waiting for input..."
        self.logs: List[str] = []
        self.max_logs = 10
        
        # Needs State (Mock default, should be updated by agent)
        self.needs = {
            "health": 100,
            "energy": 100,
            "social": 50
        }
        
        # Initialize Layout
        self._setup_layout()

    def _setup_layout(self):
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=3)
        )
        
        # Split body into sidebar (stats) and main (activity)
        self.layout["body"].split_row(
            Layout(name="sidebar", size=35),
            Layout(name="main", ratio=1)
        )
        
        # Split sidebar into System and Needs
        self.layout["sidebar"].split_column(
            Layout(name="system", size=10),
            Layout(name="needs", ratio=1)
        )

    def update_state(self, state: str, task: str = None):
        """Update agent state (IDLE, THINKING, ACTING, SLEEPING)."""
        self.agent_state = state
        if task:
            self.current_task = task

    def update_needs(self, needs_data: Dict[str, float]):
        """Update needs values."""
        self.needs.update(needs_data)

    def log(self, message: str):
        """Add a log entry."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")
        if len(self.logs) > self.max_logs:
            self.logs.pop(0)

    def _get_header(self) -> Panel:
        """Render Header"""
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="right")
        
        status_color = "green" if self.agent_state != "SLEEPING" else "blue"
        status_icon = "●" if self.agent_state != "SLEEPING" else "☾"
        
        grid.add_row(
            "[b bold cyan]🤖 AGENT OMNI-MONITOR[/]",
            f"🕒 {datetime.now().strftime('%H:%M:%S')} | [{status_color}]{status_icon} {self.agent_state}[/]"
        )
        return Panel(grid, style="white on blue")

    def _get_system_stats(self) -> Panel:
        """Render System Stats"""
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        
        # Create a grid for stats
        grid = Table.grid(expand=True)
        grid.add_column(ratio=1)
        grid.add_column(justify="right")
        
        # CPU Row
        cpu_color = "green" if cpu < 60 else ("yellow" if cpu < 85 else "red")
        grid.add_row(f"CPU: [{cpu_color}]{cpu}%[/]")
        
        # Memory Row
        mem_color = "green" if mem < 60 else ("yellow" if mem < 85 else "red")
        grid.add_row(f"MEM: [{mem_color}]{mem}%[/]")
        
        return Panel(
            grid,
            title="[bold blue]SYSTEM[/]",
            border_style="blue"
        )

    def _get_needs_panel(self) -> Panel:
        """Render Biological Needs"""
        grid = Table.grid(expand=True, padding=(0, 1))
        grid.add_column(justify="right", width=8) # Label
        grid.add_column(ratio=1) # Bar
        grid.add_column(justify="right", width=5) # Value
        
        # Helper to render bar
        def render_bar(label, value, color, icon):
            width = 15
            filled = int((value / 100) * width)
            bar = f"[{color}]{'█' * filled}[/][dim white]{'░' * (width - filled)}[/]"
            grid.add_row(f"{icon} {label}", bar, f"{int(value)}%")

        render_bar("Health", self.needs.get("health", 100), "red", "❤️")
        render_bar("Energy", self.needs.get("energy", 100), "yellow", "⚡")
        render_bar("Social", self.needs.get("social", 50), "blue", "💬")
        
        return Panel(
            grid,
            title="[bold red]VITALS[/]",
            border_style="red"
        )

    def _get_activity_panel(self) -> Panel:
        """Render Main Activity Area"""
        # Determine styling based on state
        color = "white"
        if self.agent_state == "THINKING": color = "magenta"
        elif self.agent_state == "ACTING": color = "green"
        elif self.agent_state == "SLEEPING": color = "blue"
        
        # Current Task Display
        task_text = Text(self.current_task, style=f"bold {color}")
        
        # Log Display
        log_text = Text()
        for log in self.logs:
            log_text.append(log + "\n", style="dim white")
            
        # Combine
        content = Layout()
        content.split_column(
            Layout(Panel(task_text, title="Current Focus", border_style=color), size=5),
            Layout(Panel(log_text, title="Activity Log", border_style="dim white"))
        )
        
        return Panel(
            content,
            title=f"[bold {color}]AGENT ACTIVITY: {self.agent_state}[/]",
            border_style=color
        )

    def _get_footer(self) -> Panel:
        return Panel(
            Align.center("[dim]Press Ctrl+C to stop monitor[/]"),
            style="black on white"
        )

    def start(self):
        """Start the monitor loop in a separate thread (for demo purposes) or blocking."""
        self.running = True
        try:
            with Live(self.layout, refresh_per_second=4, screen=True) as live:
                while self.running:
                    self.layout["header"].update(self._get_header())
                    self.layout["system"].update(self._get_system_stats())
                    self.layout["needs"].update(self._get_needs_panel())
                    self.layout["main"].update(self._get_activity_panel())
                    self.layout["footer"].update(self._get_footer())
                    time.sleep(0.25)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.running = False
        print("Monitor stopped.")

# Demo run
if __name__ == "__main__":
    monitor = AgentMonitor()
    # Simulate some activity in background
    def simulate_agent():
        states = ["IDLE", "THINKING", "ACTING", "SLEEPING"]
        tasks = [
            "Analyzing user request...",
            "Scanning file system...",
            "Writing code to src/main.py...",
            "Consolidating memories (Dreaming)..."
        ]
        while monitor.running:
            state = random.choice(states)
            monitor.update_state(state, random.choice(tasks))
            monitor.update_needs({
                "energy": max(0, min(100, monitor.needs["energy"] + random.randint(-5, 5))),
                "health": max(0, min(100, monitor.needs["health"] + random.randint(-1, 1)))
            })
            monitor.log(f"State changed to {state}")
            time.sleep(2)
            
    t = threading.Thread(target=simulate_agent)
    t.daemon = True
    t.start()
    
    monitor.start()
