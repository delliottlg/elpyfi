#!/usr/bin/env python3
"""
Secrets Manager for PM Claude
Handles loading, validating, and distributing secrets to services
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, SecretStr, Field, field_validator
from pydantic_settings import BaseSettings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServiceSecrets(BaseModel):
    """Base model for service-specific secrets"""
    database_url: Optional[SecretStr] = None
    
    def get_env_vars(self, prefix: str = "") -> Dict[str, str]:
        """Convert secrets to environment variables with optional prefix"""
        env_vars = {}
        for key, value in self.model_dump(exclude_none=True).items():
            if value is not None:
                env_key = f"{prefix}{key.upper()}" if prefix else key.upper()
                # Handle SecretStr values
                env_value = value.get_secret_value() if hasattr(value, 'get_secret_value') else str(value)
                env_vars[env_key] = env_value
        return env_vars


class CoreSecrets(ServiceSecrets):
    """Secrets for Core Trading Engine"""
    alpaca_api_key: SecretStr
    alpaca_secret_key: SecretStr
    alpaca_base_url: str = "https://paper-api.alpaca.markets"


class AISecrets(ServiceSecrets):
    """Secrets for AI Service"""
    anthropic_api_key: Optional[SecretStr] = None
    openai_api_key: Optional[SecretStr] = None
    
    @field_validator('anthropic_api_key', 'openai_api_key')
    def at_least_one_ai_key(cls, v, info):
        """Ensure at least one AI API key is provided"""
        if not v and not any(info.data.get(k) for k in ['anthropic_api_key', 'openai_api_key']):
            raise ValueError("At least one AI API key must be provided")
        return v


class APISecrets(ServiceSecrets):
    """Secrets for API Service"""
    api_keys: List[str] = Field(default_factory=list)
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000"])


class DashboardSecrets(ServiceSecrets):
    """Secrets for Dashboard"""
    api_base_url: str = "http://localhost:9002"
    websocket_url: str = "ws://localhost:9002"


class MasterSecrets(BaseModel):
    """Master secrets configuration"""
    # Database (shared)
    database_url: SecretStr
    
    # Service-specific
    alpaca_api_key: SecretStr
    alpaca_secret_key: SecretStr
    alpaca_base_url: str = "https://paper-api.alpaca.markets"
    
    anthropic_api_key: Optional[SecretStr] = None
    openai_api_key: Optional[SecretStr] = None
    
    api_keys: List[str] = Field(default_factory=list)
    
    # Environment overrides
    environment: str = "development"
    log_level: str = "INFO"


class SecretsManager:
    """Manages secrets loading and distribution"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.secrets_file = config_dir / "secrets.yaml"
        self.master_secrets: Optional[MasterSecrets] = None
        
    def load_secrets(self, environment: Optional[str] = None) -> MasterSecrets:
        """Load secrets from file with environment overrides"""
        if not self.secrets_file.exists():
            raise FileNotFoundError(
                f"Secrets file not found at {self.secrets_file}. "
                "Copy secrets.yaml.example to secrets.yaml and fill in your values."
            )
        
        with open(self.secrets_file) as f:
            data = yaml.safe_load(f)
        
        # Apply environment-specific overrides
        env = environment or data.get('environment', 'development')
        if 'environments' in data and env in data['environments']:
            env_data = data['environments'][env]
            data.update(env_data)
        
        self.master_secrets = MasterSecrets(**data)
        logger.info(f"Loaded secrets for environment: {env}")
        return self.master_secrets
    
    def get_service_secrets(self, service: str) -> ServiceSecrets:
        """Get secrets for a specific service"""
        if not self.master_secrets:
            raise RuntimeError("Secrets not loaded. Call load_secrets() first.")
        
        if service == "elpyfi-core":
            return CoreSecrets(
                database_url=self.master_secrets.database_url,
                alpaca_api_key=self.master_secrets.alpaca_api_key,
                alpaca_secret_key=self.master_secrets.alpaca_secret_key,
                alpaca_base_url=self.master_secrets.alpaca_base_url
            )
        
        elif service == "elpyfi-ai":
            return AISecrets(
                database_url=self.master_secrets.database_url,
                anthropic_api_key=self.master_secrets.anthropic_api_key,
                openai_api_key=self.master_secrets.openai_api_key
            )
        
        elif service == "elpyfi-api":
            return APISecrets(
                database_url=self.master_secrets.database_url,
                api_keys=self.master_secrets.api_keys
            )
        
        elif service == "elpyfi-dashboard":
            return DashboardSecrets()
        
        else:
            raise ValueError(f"Unknown service: {service}")
    
    def get_service_env_vars(self, service: str, prefix: str = "") -> Dict[str, str]:
        """Get environment variables for a service"""
        secrets = self.get_service_secrets(service)
        
        # Special handling for dashboard (Next.js needs NEXT_PUBLIC_ prefix)
        if service == "elpyfi-dashboard" and not prefix:
            prefix = "NEXT_PUBLIC_"
        
        return secrets.get_env_vars(prefix)
    
    def validate_all_services(self) -> Dict[str, bool]:
        """Validate secrets for all services"""
        if not self.master_secrets:
            self.load_secrets()
        
        results = {}
        services = ["elpyfi-core", "elpyfi-ai", "elpyfi-api", "elpyfi-dashboard"]
        
        for service in services:
            try:
                self.get_service_secrets(service)
                results[service] = True
                logger.info(f"✅ {service}: Secrets valid")
            except Exception as e:
                results[service] = False
                logger.error(f"❌ {service}: {str(e)}")
        
        return results


def main():
    """Test secrets loading and validation"""
    from pathlib import Path
    
    config_dir = Path(__file__).parent.parent / "config"
    manager = SecretsManager(config_dir)
    
    try:
        # Load secrets
        secrets = manager.load_secrets()
        print(f"\n🔐 Loaded secrets for environment: {secrets.environment}")
        
        # Validate all services
        print("\n📋 Validating service secrets:")
        results = manager.validate_all_services()
        
        # Show example env vars for each service
        print("\n🔧 Example environment variables:")
        for service in ["elpyfi-core", "elpyfi-ai", "elpyfi-api", "elpyfi-dashboard"]:
            env_vars = manager.get_service_env_vars(service)
            print(f"\n{service}:")
            for key, value in list(env_vars.items())[:3]:  # Show first 3
                masked_value = value[:4] + "..." if len(value) > 4 else "***"
                print(f"  {key}={masked_value}")
    
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\n📝 Creating example secrets file...")
        example_file = config_dir / "secrets.yaml.example"
        if example_file.exists():
            print(f"Copy {example_file} to {config_dir / 'secrets.yaml'} and fill in your values.")


if __name__ == "__main__":
    main()