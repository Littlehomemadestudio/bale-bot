"""
Configuration settings for Admiral's Gambit Arcade
"""
import os


class Config:
    """Bot configuration constants"""
    
    # Bot token
    TOKEN = "1412654976:5jFsvZkab1Bq-2vSJ08Nzg9C3DHuBkYQkQU"
    
    # Data file path
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    DATA_FILE = os.path.join(DATA_DIR, "arcade_data.json")
    
    # Rate limiting
    MESSAGE_RATE_LIMIT = {"max_calls": 30, "time_window": 60}
    ACTION_RATE_LIMIT = {"max_calls": 10, "time_window": 30}
    
    # Cute message interval (seconds)
    CUTE_MESSAGE_INTERVAL = 1800  # 30 minutes
