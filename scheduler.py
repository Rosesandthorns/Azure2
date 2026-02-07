import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional
import random


@dataclass
class SchedulerConfig:
    inactivity_minutes: int
    curiosity_trigger_count: int
    cooldown_minutes: int
    boredom_decay_minutes: int
    boredom_increase_on_interaction: float
    # Proactive DM settings (from Azure-improved)
    enable_proactive_dms: bool = False
    dm_inactivity_hours: int = 24
    dm_max_per_user_per_day: int = 1
    dm_cooldown_hours: int = 12


class Scheduler:
    def __init__(self, config: SchedulerConfig) -> None:
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.last_user_message = datetime.utcnow()
        self.last_proactive: Optional[datetime] = None
        self.curiosity_count = 0
        self.boredom = 10.0
        self.last_boredom_tick = datetime.utcnow()
        self.last_proactive_topic: Optional[str] = None
        self.modes = [
            "curious",
            "analytical",
            "concise",
            "structured",
            "cautious",
            "exploratory",
        ]
        # Proactive DM tracking (from Azure-improved)
        self.last_dm_sent: Dict[str, datetime] = {}
        self.dm_count_today: Dict[str, int] = {}
        self.last_day_reset = datetime.utcnow().date()

    def update_on_message(self) -> None:
        self.last_user_message = datetime.utcnow()
        self.boredom = min(10.0, self.boredom + self.config.boredom_increase_on_interaction)

    def register_curiosity(self) -> None:
        self.curiosity_count += 1

    def tick(self) -> None:
        now = datetime.utcnow()
        if now - self.last_boredom_tick < timedelta(minutes=self.config.boredom_decay_minutes):
            return
        self.last_boredom_tick = now
        self.boredom = max(0.0, self.boredom - 1.0)

    def should_proactively_speak(self, topic: str, probability: float) -> bool:
        now = datetime.utcnow()
        if self.last_proactive and now - self.last_proactive < timedelta(
            minutes=self.config.cooldown_minutes
        ):
            return False
        if topic == self.last_proactive_topic:
            probability *= 0.5
        probability = min(1.0, max(0.0, probability))
        return random.random() < probability

    def record_proactive(self, topic: str) -> None:
        self.last_proactive = datetime.utcnow()
        self.curiosity_count = 0
        self.last_proactive_topic = topic

    def should_dm(self) -> bool:
        return self.boredom <= 3.0

    def current_mode(self) -> str:
        index = int((10.0 - self.boredom) // 2)
        index = max(0, min(index, len(self.modes) - 1))
        return self.modes[index]
    
    # ==================== Proactive DM Methods (from Azure-improved) ====================
    
    def should_send_proactive_dm(self, user_id: str, last_interaction: datetime) -> bool:
        """Check if bot should send a proactive DM to a specific user"""
        if not self.config.enable_proactive_dms:
            return False
        
        now = datetime.utcnow()
        
        # Reset daily counters if it's a new day
        if now.date() > self.last_day_reset:
            self.dm_count_today.clear()
            self.last_day_reset = now.date()
        
        # Check daily limit
        if self.dm_count_today.get(user_id, 0) >= self.config.dm_max_per_user_per_day:
            return False
        
        # Check cooldown
        if user_id in self.last_dm_sent:
            time_since_last_dm = now - self.last_dm_sent[user_id]
            if time_since_last_dm < timedelta(hours=self.config.dm_cooldown_hours):
                return False
        
        # Check inactivity
        time_since_interaction = now - last_interaction
        if time_since_interaction < timedelta(hours=self.config.dm_inactivity_hours):
            return False
        
        return True
    
    def record_dm_sent(self, user_id: str) -> None:
        """Record that a proactive DM was sent to a user"""
        now = datetime.utcnow()
        self.last_dm_sent[user_id] = now
        self.dm_count_today[user_id] = self.dm_count_today.get(user_id, 0) + 1
