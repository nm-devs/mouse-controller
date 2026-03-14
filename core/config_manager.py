import json
import os
import config as default_config

SETTINGS_FILE = 'settings.json'

class ConfigManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
        
    def _load_config(self):
        # Load defaults from config.py
        self.settings = {
            'DETECTION_CONFIDENCE': default_config.DETECTION_CONFIDENCE,
            'TRACKING_CONFIDENCE': default_config.TRACKING_CONFIDENCE,
            'SMOOTHING_ALPHA': default_config.SMOOTHING_ALPHA,
            'PINCH_DISTANCE': default_config.PINCH_DISTANCE,
            'SCROLL_JITTER_THRESHOLD': default_config.SCROLL_JITTER_THRESHOLD,
            'SCROLL_SPEED_MULTIPLIER_X': getattr(default_config, 'SCROLL_SPEED_MULTIPLIER_X', 1.5),
            'SCROLL_SPEED_MULTIPLIER_Y': getattr(default_config, 'SCROLL_SPEED_MULTIPLIER_Y', 1.5),
            'SMOOTHING_WINDOW_SIZE': default_config.SMOOTHING_WINDOW_SIZE,
            'SMOOTHING_DOMINANCE_THRESHOLD': default_config.SMOOTHING_DOMINANCE_THRESHOLD,
            'CONFIDENCE_THRESHOLD': default_config.CONFIDENCE_THRESHOLD
        }
        
        # Override with JSON if exists
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    saved_settings = json.load(f)
                    for k, v in saved_settings.items():
                        if k in self.settings:
                            self.settings[k] = v
            except Exception as e:
                print(f"Error loading settings.json: {e}")

    def save_config(self):
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(self.settings, f, indent=4)
            print("Settings saved successfully!")
        except Exception as e:
            print(f"Error saving settings.json: {e}")
            
    def get(self, key):
        return self.settings.get(key, getattr(default_config, key, None))
        
    def set(self, key, value):
        if key in self.settings:
            self.settings[key] = value

# Global instance for easy access
config_mgr = ConfigManager()
