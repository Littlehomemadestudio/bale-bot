"""
Data loading and player management for Admiral's Gambit Arcade
"""
import json
import os
from typing import Dict, Any

from .config import Config


class DataLoader:
    """Handles loading and saving game data"""
    
    def __init__(self):
        self.data_file = Config.DATA_FILE
        self.arcade_data = {}
        
    def ensure_data_dir(self):
        """Ensure the data directory exists"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
    
    def load_data(self) -> Dict[str, Any]:
        """Load arcade data from file"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.arcade_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.arcade_data = {}
        return self.arcade_data
    
    def save_data(self) -> bool:
        """Save arcade data to file"""
        try:
            self.ensure_data_dir()
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.arcade_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False
    
    def get_player(self, user_id: str) -> Dict[str, Any]:
        """
        Get or create player data
        
        Args:
            user_id: User identifier
            
        Returns:
            Player data dictionary
        """
        uid = str(user_id)
        if uid not in self.arcade_data:
            self.arcade_data[uid] = {
                "credits": 5000,
                "prestige": 0,
                "rank": 0,
                "wins": 0,
                "losses": 0,
                "kill_streak": 0,
                "best_streak": 0,
                "ships": [],
                "inventory": [],
                "total_damage_dealt": 0,
                "total_damage_taken": 0,
                "trophies": [],
                "module_crates": 0,
                "prestige_tokens": 0,
            }
        return self.arcade_data[uid]


# Global data loader instance
data_loader = DataLoader()


def load_data():
    """Legacy function - use DataLoader instead"""
    return data_loader.load_data()


def save_data():
    """Legacy function - use DataLoader instead"""
    return data_loader.save_data()


def get_player(user_id: str) -> Dict[str, Any]:
    """Legacy function - use DataLoader instead"""
    return data_loader.get_player(user_id)
