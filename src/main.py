#!/usr/bin/env python3
"""
Main entry point for the DNS updater.
"""
import logging
import os
import sys
import time
from typing import Optional, Type

from updater import DNSProvider, DNSUpdater, DNSRecord
from plugins import CloudflareProvider

def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def get_provider_class(provider_name: str) -> Optional[Type[DNSProvider]]:
    """
    Get the provider class based on the provider name.
    
    Args:
        provider_name: Name of the provider to use
        
    Returns:
        DNSProvider class or None if provider not found
    """
    # This could be extended to load providers dynamically from a plugins directory
    providers = {
        "cloudflare": CloudflareProvider
    }
    
    provider_class = providers.get(provider_name.lower())
    if not provider_class:
        logging.error(f"Unknown provider: {provider_name}")
        return None
        
    return provider_class

def get_provider(provider_name: str) -> Optional[DNSUpdater]:
    """
    Get the appropriate DNS provider based on configuration.
    
    Args:
        provider_name: Name of the provider to use
        
    Returns:
        DNSUpdater instance or None if provider not found
    """
    provider_class = get_provider_class(provider_name)
    if not provider_class:
        return None
        
    try:
        config_class = provider_class.get_config_class()
        config = config_class.from_env()
        provider = provider_class(config)
        return DNSUpdater(provider)
    except ValueError as e:
        logging.error(f"Configuration error: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Failed to initialize provider: {str(e)}")
        return None

def main():
    """Main entry point."""
    # Get configuration from environment variables
    provider_name = os.getenv("PROVIDER", "cloudflare")
    records_str = os.getenv("DNS_RECORDS", os.getenv("DNS_RECORD", ""))  # Support both DNS_RECORDS and DNS_RECORD for backward compatibility
    interval = int(os.getenv("INTERVAL", "300"))
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    # Parse DNS records - support comma-separated list
    records = [record.strip() for record in records_str.split(",") if record.strip()]
    
    if not records:
        logging.error("DNS_RECORDS or DNS_RECORD environment variable is required")
        return 1
    
    setup_logging(log_level)
    
    updater = get_provider(provider_name)
    if not updater:
        return 1
    
    logging.info(f"Starting DNS updater for records {records} using {provider_name}")
    
    while True:
        try:
            # Get the current IP address
            current_ip = updater.provider.get_current_ip()
            
            # Process each DNS record
            for record in records:
                try:
                    # Get the current DNS record
                    current_record = updater.provider.get_dns_record(record)
                    
                    if not current_record:
                        logging.info(f"Creating new DNS record for {record}")
                        new_record = DNSRecord(
                            name=record,
                            content=current_ip,
                            type="A",
                            ttl=1
                        )
                        updater.provider.update_dns_record(new_record)
                    else:
                        if current_record.content != current_ip:
                            logging.info(f"Updating {record} from {current_record.content} to {current_ip}")
                            new_record = DNSRecord(
                                name=record,
                                content=current_ip,
                                type=current_record.type,
                                ttl=current_record.ttl,
                                id=current_record.id
                            )
                            updater.provider.update_dns_record(new_record)
                        else:
                            logging.debug(f"IP {current_ip} matches current record for {record}, no update needed")
                except Exception as e:
                    logging.error(f"Error processing record {record}: {str(e)}")
                    continue  # Continue with next record even if one fails
            
            time.sleep(interval)
        except KeyboardInterrupt:
            logging.info("Shutting down...")
            break
        except Exception as e:
            logging.error(f"Error in main loop: {str(e)}")
            time.sleep(interval)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
