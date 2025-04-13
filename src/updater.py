"""
Main updater class for dynamic DNS updates.
"""
import abc
import logging
import re
from typing import Optional, Type

import requests
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ProviderConfig(BaseModel):
    """Base configuration class for DNS providers."""
    @classmethod
    def from_env(cls) -> 'ProviderConfig':
        """Load configuration from environment variables."""
        raise NotImplementedError("Providers must implement from_env()")

class DNSRecord(BaseModel):
    """DNS record model."""
    name: str
    content: str
    type: str = "A"
    ttl: int = 1
    id: Optional[str] = None

class DNSProvider(abc.ABC):
    """Abstract base class for DNS providers."""
    
    @classmethod
    @abc.abstractmethod
    def get_config_class(cls) -> Type[ProviderConfig]:
        """Get the configuration class for this provider."""
        pass
    
    def get_current_ip(self) -> str:
        """
        Get the current public IP address using multiple IP detection services.
        This is a generic implementation that can be overridden by providers if needed.
        """
        try:
            # Try multiple IP detection services
            services = [
                "https://ifconfig.co/ip",  # Returns just the IP
                "https://api.ipify.org",   # Simple IP service
                "https://icanhazip.com"    # Another reliable service
            ]
            
            for service in services:
                try:
                    response = requests.get(service, timeout=5)
                    response.raise_for_status()
                    ip = response.text.strip()
                    
                    # Validate that it's a valid IPv4 address
                    if re.match(r'^(\d{1,3}\.){3}\d{1,3}$', ip):
                        # Additional validation for each octet
                        octets = ip.split('.')
                        if all(0 <= int(octet) <= 255 for octet in octets):
                            logger.debug(f"[{service}] Detected IP address: {ip}")
                            return ip
                except Exception as e:
                    logger.warning(f"[{service}] Failed to get IP: {str(e)}")
                    continue
            
            # If all services fail, try a more direct approach
            response = requests.get("https://ifconfig.co", timeout=5)
            response.raise_for_status()
            ip = response.text.strip()
            
            # Try to extract an IPv4 address from the response
            ipv4_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', ip)
            if ipv4_match:
                ip = ipv4_match.group(1)
                # Validate each octet
                octets = ip.split('.')
                if all(0 <= int(octet) <= 255 for octet in octets):
                    logger.debug(f"Extracted IP address: {ip}")
                    return ip
            
            raise ValueError(f"Could not extract a valid IPv4 address from: {ip}")
            
        except Exception as e:
            logger.error(f"Error getting current IP: {str(e)}")
            raise RuntimeError("Failed to determine current IP address after trying all available services") from e
    
    @abc.abstractmethod
    def get_dns_record(self, record_name: str) -> Optional[DNSRecord]:
        """Get the current DNS record."""
        pass
    
    @abc.abstractmethod
    def update_dns_record(self, record: DNSRecord) -> bool:
        """Update the DNS record."""
        pass

class DNSUpdater:
    """Main DNS updater class."""
    
    def __init__(self, provider: DNSProvider):
        self.provider = provider
    
    def update(self, record_name: str) -> bool:
        """
        Update the DNS record if necessary.
        
        Args:
            record_name: The name of the DNS record to update
            
        Returns:
            bool: True if update was successful or not needed, False if update failed
        """
        try:
            current_ip = self.provider.get_current_ip()
            current_record = self.provider.get_dns_record(record_name)
            
            if not current_record:
                logger.info(f"Creating new DNS record for {record_name}")
                new_record = DNSRecord(
                    name=record_name,
                    content=current_ip,
                    type="A",
                    ttl=1,
                )
                return self.provider.update_dns_record(new_record)
                
            if current_record.content == current_ip:
                logger.debug(f"IP {current_ip} match current record, no update needed")
                return True

            logger.info(f"Updating {record_name} from {current_record.content} to {current_ip}")
            new_record = DNSRecord(
                name=record_name,
                content=current_ip,
                type=current_record.type,
                ttl=current_record.ttl,
                id=current_record.id
            )
            
            return self.provider.update_dns_record(new_record)
            
        except Exception as e:
            logger.error(f"Error updating DNS record: {str(e)}")
            return False 
