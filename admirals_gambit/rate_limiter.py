"""
Rate limiter for controlling message and action frequency
"""
import time
from collections import deque


class RateLimiter:
    """Controls rate of actions per user within a time window"""
    
    def __init__(self, max_calls: int = 20, time_window: int = 60):
        """
        Initialize rate limiter
        
        Args:
            max_calls: Maximum number of calls allowed in the time window
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = {}
    
    async def check(self, user_id) -> float:
        """
        Check if user has exceeded rate limit
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Wait time in seconds (0 if allowed)
        """
        now = time.time()
        uid = str(user_id)
        
        if uid not in self.calls:
            self.calls[uid] = deque()
        
        # Clean old calls
        while self.calls[uid] and self.calls[uid][0] < now - self.time_window:
            self.calls[uid].popleft()
        
        if len(self.calls[uid]) >= self.max_calls:
            wait_time = self.calls[uid][0] + self.time_window - now
            return wait_time
        
        self.calls[uid].append(now)
        return 0
