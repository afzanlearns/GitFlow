import pytest
from pathlib import Path
from gitflow.config import Config, DEFAULT_CONFIG

def test_config_singleton():
    c1 = Config()
    c2 = Config()
    assert c1 is c2

def test_config_load_and_save(tmp_path):
    config_file = tmp_path / "subdir" / "config.yml"
    Config._config = {} # clear to force reloading and saving default config
    Config._config_path = config_file # Set class attribute directly
    
    # Check singleton path load
    c = Config(config_file)
    assert c._config_path == config_file
    assert config_file.exists() # default config was saved since it didn't exist
    
    # Modify config and save
    cfg = Config.load(config_file)
    cfg['gitflow']['scrape_interval_hours'] = 5
    Config.save(cfg, config_file)
    
    # Load again to check
    new_cfg = Config.load(config_file)
    assert new_cfg['gitflow']['scrape_interval_hours'] == 5

def test_config_get():
    # Set to a known config dictionary
    Config._config = {
        'a': {
            'b': 123
        }
    }
    assert Config.get('a.b') == 123
    assert Config.get('a.c', 'default_val') == 'default_val'
    assert Config.get('nonexistent', 'default_val') == 'default_val'
    assert Config.get('a.b.c', 'default_val') == 'default_val'

def test_config_validate():
    # Valid config
    Config._config = {
        'gitflow': {
            'scrape_interval_hours': 1,
            'database_path': '/tmp/db.db',
        },
        'analytics': {
            'productivity_threshold': 80,
            'streak_reset_days': 1,
        },
        'scheduler': {
            'daily_stats_time': '00:01',
            'daily_digest_time': '08:00',
        }
    }
    assert Config.validate() is True
    
    # Incomplete config (non-empty so it doesn't auto-load default, but lacks required keys)
    Config._config = {'gitflow': {}}
    assert Config.validate() is False
    
    # Invalid scrape_interval
    Config._config = {
        'gitflow': {
            'scrape_interval_hours': 0, # invalid, must be >= 1
            'database_path': '/tmp/db.db',
        },
        'analytics': {
            'productivity_threshold': 80,
            'streak_reset_days': 1,
        },
        'scheduler': {
            'daily_stats_time': '00:01',
            'daily_digest_time': '08:00',
        }
    }
    assert Config.validate() is False

def test_config_reset(tmp_path):
    config_file = tmp_path / "config.yml"
    Config._config_path = config_file
    Config.reset()
    assert config_file.exists()
    assert Config._config['gitflow']['scrape_interval_hours'] == 1
