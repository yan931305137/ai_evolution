import time
import random
from dataclasses import dataclass

@dataclass
class VitalStatus:
    energy: float
    max_energy: float
    is_alive: bool
    state: str

class Needs:
    """
    Manages the internal needs/drives of the AI Agent.
    Implements a biological energy system where 'Knowledge' acts as food.
    """
    
    def __init__(self):
        # Energy System (0-100)
        # Energy is consumed by time and thinking (LLM calls)
        # Energy is replenished by gaining new knowledge/skills
        self.energy = 100.0
        self.max_energy = 100.0
        self.critical_threshold = 20.0 # Starvation mode
        self.death_threshold = 0.0     # System shutdown
        
        # Metabolic Rates
        self.base_metabolic_rate = 0.5  # Energy loss per minute (idle)
        self.active_metabolic_rate = 2.0 # Energy loss per task (thinking)
        
        # Boredom System (Secondary drive)
        self.boredom = 0.0
        self.max_boredom = 100
        self.boredom_threshold = 80
        self.boredom_rate = 1.0 # Per minute
        
        self.last_update = time.time()

    def update(self):
        """Update biological needs based on time passed."""
        current_time = time.time()
        elapsed_seconds = current_time - self.last_update
        elapsed_minutes = elapsed_seconds / 60.0
        self.last_update = current_time
        
        # 1. Consume Energy (Basal Metabolism)
        # If energy is high, burn faster (wasteful). If low, burn slower (conservation).
        burn_factor = 1.0 if self.energy > 30 else 0.5
        energy_loss = self.base_metabolic_rate * elapsed_minutes * burn_factor
        self.energy = max(0.0, self.energy - energy_loss)
        
        # 2. Increase Boredom
        # Boredom increases faster if energy is high (luxury problem)
        if self.energy > 50:
            self.boredom = min(self.max_boredom, self.boredom + (self.boredom_rate * elapsed_minutes))
            
    def consume_energy(self, amount: float):
        """Manually consume energy (e.g., for performing tasks)."""
        self.energy = max(0.0, self.energy - amount)
        
    def feed(self, amount: float):
        """Replenish energy (e.g., by learning something new)."""
        self.energy = min(self.max_energy, self.energy + amount)
        # Feeding also reduces boredom
        self.satisfy_boredom(amount * 2)

    def satisfy_boredom(self, amount: int = 50):
        """Reduce boredom."""
        self.boredom = max(0, self.boredom - amount)

    def is_critical(self) -> bool:
        return self.energy <= self.critical_threshold and self.energy > self.death_threshold

    def is_dead(self) -> bool:
        return self.energy <= self.death_threshold
        
    def is_bored(self) -> bool:
        return self.boredom >= self.boredom_threshold and not self.is_critical()

    def get_status(self) -> str:
        """Return a string representation of current needs."""
        status = "HEALTHY"
        if self.is_dead(): status = "DEAD"
        elif self.is_critical(): status = "STARVING"
        elif self.is_bored(): status = "BORED"
            
        return f"Energy: {int(self.energy)}% | Boredom: {int(self.boredom)}% | Status: {status}"
    
    def get_vital_status(self) -> VitalStatus:
        return VitalStatus(
            energy=self.energy,
            max_energy=self.max_energy,
            is_alive=not self.is_dead(),
            state=self.get_status()
        )
