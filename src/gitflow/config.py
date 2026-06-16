from pathlib import Path
from typing import Any, Dict, Optional
import yaml
import os
import logging

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_DIR = Path.home() / '.gitflow'
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / 'config.yml'

DEFAULT_CONFIG = {
    'gitflow': {
        'scrape_interval_hours': 1,
        'database_path': str(DEFAULT_CONFIG_DIR / 'gitflow.db'),
    },
    'notifications': {
        'enabled': True,
        'slack_webhook': None,
        'email_enabled': False,
        'email_address': None,
        'smtp_host': 'smtp.gmail.com',
        'smtp_port': 587,
        'smtp_username': None,
        'smtp_user': None,
        'smtp_password': None,
    },
    'analytics': {
        'productivity_threshold': 80,
        'streak_reset_days': 1,
    },
    'scheduler': {
        'daily_stats_time': '00:01',
        'daily_digest_time': '08:00',
    },
    'ui': {
        'theme': 'dark',
    },
    'rate_limiting': {
        'enabled': True,
        'default_limit': '10/minute',
    },
}


class Config:
    _instance = None
    _config: Dict[str, Any] = {}
    _config_path: Path = DEFAULT_CONFIG_PATH

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_path: Optional[Path] = None):
        if config_path:
            self._config_path = Path(config_path)
        if not self._config:
            self._config = self.load()

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> Dict[str, Any]:
        if config_path:
            path = Path(config_path)
        else:
            path = cls._config_path

        import copy
        config = copy.deepcopy(DEFAULT_CONFIG)

        if path.exists():
            try:
                with open(path, 'r') as f:
                    user_config = yaml.safe_load(f) or {}
                cls._deep_merge(config, user_config)
                logger.info(f"Loaded config from {path}")
            except Exception as e:
                logger.error(f"Error loading config from {path}: {e}")
        else:
            logger.info(f"No config file at {path}, using defaults")
            cls.save(config, path)

        cls._config = config
        cls._config_path = path
        return config

    @classmethod
    def save(cls, config_dict: Dict[str, Any], config_path: Optional[Path] = None) -> None:
        path = config_path or cls._config_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)
        logger.info(f"Saved config to {path}")

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        if not cls._config:
            cls.load()

        keys = key.split('.')
        value = cls._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value

    @classmethod
    def validate(cls) -> bool:
        required_keys = [
            'gitflow.scrape_interval_hours',
            'gitflow.database_path',
            'analytics.productivity_threshold',
            'analytics.streak_reset_days',
            'scheduler.daily_stats_time',
            'scheduler.daily_digest_time',
        ]

        if not cls._config:
            cls.load()

        for key in required_keys:
            if cls.get(key) is None:
                logger.error(f"Missing required config key: {key}")
                return False

        scrape_interval = cls.get('gitflow.scrape_interval_hours')
        if not isinstance(scrape_interval, (int, float)) or scrape_interval < 1:
            logger.error(f"Invalid scrape_interval_hours: {scrape_interval}")
            return False

        return True

    @classmethod
    def reset(cls) -> None:
        import copy
        cls._config = copy.deepcopy(DEFAULT_CONFIG)
        cls.save(cls._config)

    @staticmethod
    def _deep_merge(base: Dict, override: Dict) -> None:
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                Config._deep_merge(base[key], value)
            else:
                base[key] = value
