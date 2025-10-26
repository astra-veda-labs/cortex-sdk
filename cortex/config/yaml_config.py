"""
YAML Configuration Manager for Cortex SDK

Simple YAML-based configuration for switching between in-memory and Chroma backends.
"""

import yaml
import os
from typing import Dict, Any, Optional
from enum import Enum


class BackendType(Enum):
    """Supported backend types"""
    IN_MEMORY = "in_memory"
    CHROMA = "chroma"


class YAMLConfig:
    """YAML-based configuration manager"""
    
    def __init__(self, config_file: str = "cortex_config.yaml"):
        """
        Initialize YAML configuration
        
        Args:
            config_file: Path to YAML configuration file
        """
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                print(f"Error loading config file {self.config_file}: {e}")
                return self._create_default_config()
        else:
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration"""
        return {
            "backend": "in_memory",
            "backends": {
                "in_memory": {
                    "enabled": True,
                    "config": {
                        "capacity": 1000,
                        "persistent": False
                    }
                },
                "chroma": {
                    "enabled": False,
                    "config": {
                        "persistent": False,
                        "collection_name": "cortex_memories",
                        "similarity_threshold": 0.5,
                        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
                    }
                }
            }
        }
    
    def get_current_backend(self) -> str:
        """Get current backend"""
        return self.config.get("backend", "in_memory")
    
    def get_backend_config(self, backend: str) -> Dict[str, Any]:
        """Get configuration for a specific backend"""
        return self.config.get("backends", {}).get(backend, {})
    
    def switch_to_in_memory(self):
        """Switch to in-memory backend"""
        self.config["backend"] = "in_memory"
        self.config["backends"]["in_memory"]["enabled"] = True
        self.config["backends"]["chroma"]["enabled"] = False
        self._save_config()
    
    def switch_to_chroma(self, persistent: bool = False, collection_name: str = "cortex_memories"):
        """Switch to Chroma backend"""
        self.config["backend"] = "chroma"
        self.config["backends"]["in_memory"]["enabled"] = False
        self.config["backends"]["chroma"]["enabled"] = True
        self.config["backends"]["chroma"]["config"]["persistent"] = persistent
        self.config["backends"]["chroma"]["config"]["collection_name"] = collection_name
        self._save_config()
    
    def is_backend_enabled(self, backend: str) -> bool:
        """Check if a backend is enabled"""
        return self.config.get("backends", {}).get(backend, {}).get("enabled", False)
    
    def get_backend_info(self) -> Dict[str, Any]:
        """Get backend information"""
        current_backend = self.get_current_backend()
        return {
            "current_backend": current_backend,
            "in_memory_enabled": self.is_backend_enabled("in_memory"),
            "chroma_enabled": self.is_backend_enabled("chroma"),
            "config_file": self.config_file
        }
    
    def _save_config(self):
        """Save configuration to YAML file"""
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
        except Exception as e:
            print(f"Error saving config file {self.config_file}: {e}")


# Global configuration instance
_yaml_config = None

def get_yaml_config(config_file: str = "cortex_config.yaml") -> YAMLConfig:
    """Get global YAML configuration instance"""
    global _yaml_config
    if _yaml_config is None:
        _yaml_config = YAMLConfig(config_file)
    return _yaml_config

def reset_yaml_config():
    """Reset global configuration (for testing)"""
    global _yaml_config
    _yaml_config = None
