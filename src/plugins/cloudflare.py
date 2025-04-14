"""
Cloudflare DNS provider implementation.
"""
import logging
import os
from typing import Optional

import requests
from pydantic import BaseModel

from updater import DNSProvider, ProviderConfig, DNSRecord

logger = logging.getLogger(__name__)

class CloudflareConfig(ProviderConfig):
    """Cloudflare-specific configuration."""
    zone_id: str
    api_token: str

    @classmethod
    def from_env(cls) -> 'CloudflareConfig':
        """Load Cloudflare configuration from environment variables."""
        zone_id = os.getenv("CLOUDFLARE_ZONE_ID")
        api_token = os.getenv("CLOUDFLARE_API_TOKEN")
        
        if not all([zone_id, api_token]):
            raise ValueError("Missing required Cloudflare configuration: CLOUDFLARE_ZONE_ID and CLOUDFLARE_API_TOKEN must be set")
            
        return cls(zone_id=zone_id, api_token=api_token)

class CloudflareRecord(DNSRecord):
    """Cloudflare-specific DNS record model."""
    proxied: bool = True

class CloudflareProvider(DNSProvider):
    """Cloudflare DNS provider implementation."""
    
    def __init__(self, config: CloudflareConfig):
        self.config = config
        self.base_url = "https://api.cloudflare.com/client/v4"
        self.headers = {
            "Authorization": f"Bearer {config.api_token}",
            "Content-Type": "application/json"
        }
    
    @classmethod
    def get_config_class(cls) -> type[ProviderConfig]:
        return CloudflareConfig
    
    def get_dns_record(self, record_name: str) -> Optional[CloudflareRecord]:
        """Get the current DNS record from Cloudflare."""
        url = f"{self.base_url}/zones/{self.config.zone_id}/dns_records"
        params = {"name": record_name}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data["success"] or not data["result"]:
                return None
                
            record = data["result"][0]
            return CloudflareRecord(
                name=record["name"],
                content=record["content"],
                type=record["type"],
                ttl=record["ttl"],
                proxied=record["proxied"],
                id=record["id"]
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting DNS record: {str(e)}")
            return None
    
    def create_dns_record(self, record: CloudflareRecord) -> bool:
        """Create a new DNS record in Cloudflare."""
        url = f"{self.base_url}/zones/{self.config.zone_id}/dns_records"
        
        # Format data according to Cloudflare's API requirements
        data = {
            "name": record.name,
            "content": record.content,
            "type": record.type,
            "ttl": record.ttl,
            "proxied": record.proxied
        }
        
        try:
            logger.debug(f"Creating DNS record with data: {data}")
            response = requests.post(url, headers=self.headers, json=data)
            
            # Log the response for debugging
            if not response.ok:
                logger.error(f"Cloudflare API error: {response.text}")
            
            response.raise_for_status()
            result = response.json()
            
            if result["success"]:
                logger.info(f"Created DNS record for {record.name} - {record.content}")
                return True
            else:
                logger.error(f"Failed to create DNS record: {result.get('errors', 'Unknown error')}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating DNS record: {str(e)}")
            return False
    
    def update_dns_record(self, record: DNSRecord) -> bool:
        """
        Update or create the DNS record in Cloudflare.
        
        Args:
            record: The DNS record to update
            proxied: Whether to proxy the record through Cloudflare (Cloudflare-specific)
        """
        proxied_str = os.getenv("PROXIED", "true").lower()
        proxied = proxied_str in ("true", "1", "yes", "y")
        logger.info(f"Cloudflare proxied mode: {proxied}")

        try:
            # First, try to get the existing record
            current_record = self.get_dns_record(record.name)
            
            # Convert the generic record to a Cloudflare record
            record = CloudflareRecord(
                name=record.name,
                content=record.content,
                type=record.type,
                ttl=record.ttl,
                proxied=proxied,
                id=record.id
            )
            
            if not current_record:
                logger.info(f"Record {record.name} not found, creating new record")
                return self.create_dns_record(record)
            
            # If record exists and content is different, update it
            if current_record.content != record.content or current_record.proxied != proxied:
                if not current_record.id:
                    logger.error(f"Record {record.name} exists but has no ID")
                    return False
                    
                url = f"{self.base_url}/zones/{self.config.zone_id}/dns_records/{current_record.id}"
                
                # Format data according to Cloudflare's API requirements
                data = {
                    "name": record.name,
                    "content": record.content,
                    "type": record.type,
                    "ttl": record.ttl,
                    "proxied": proxied
                }
                
                logger.debug(f"Updating DNS record with data: {data}")
                response = requests.put(url, headers=self.headers, json=data)
                
                # Log the response for debugging
                if not response.ok:
                    logger.error(f"Cloudflare API error: {response.text}")
                
                response.raise_for_status()
                result = response.json()
                
                if result["success"]:
                    logger.info(f"Updated DNS record for {record.name}")
                    return True
                else:
                    logger.error(f"Failed to update DNS record: {result.get('errors', 'Unknown error')}")
                    return False
            
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error updating DNS record: {str(e)}")
            return False 
