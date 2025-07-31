#!/usr/bin/env python3
"""
Proxy Service
Handles proxy rotation and management for avoiding rate limits
"""

import asyncio
import aiohttp
import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging


class ProxyService:
    """Service class for proxy management and rotation"""
    
    def __init__(self, proxy_api_url: str = "https://proxylist.geonode.com/api/proxy-list"):
        """Initialize proxy service
        
        Args:
            proxy_api_url: URL to fetch proxy list from
        """
        self.proxy_api_url = proxy_api_url
        self.proxies: List[Dict] = []
        self.current_proxy_index = 0
        self.failed_proxies: set = set()
        self.last_fetch_time: Optional[datetime] = None
        self.fetch_interval = timedelta(minutes=30)  # Refresh proxies every 30 minutes
        self.logger = logging.getLogger(__name__)
        
    async def fetch_proxies(self) -> bool:
        """Fetch fresh proxy list from API
        
        Returns:
            True if proxies were fetched successfully, False otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.proxy_api_url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Filter working proxies
                        working_proxies = []
                        for proxy in data.get('data', []):
                            # Only use proxies with high uptime and low latency
                            if (proxy.get('upTime', 0) > 80 and 
                                proxy.get('latency', 1000) < 500 and
                                'socks4' in proxy.get('protocols', [])):
                                
                                proxy_url = f"socks4://{proxy['ip']}:{proxy['port']}"
                                working_proxies.append({
                                    'url': proxy_url,
                                    'ip': proxy['ip'],
                                    'port': proxy['port'],
                                    'country': proxy.get('country', 'Unknown'),
                                    'uptime': proxy.get('upTime', 0),
                                    'latency': proxy.get('latency', 0)
                                })
                        
                        if working_proxies:
                            self.proxies = working_proxies
                            self.last_fetch_time = datetime.now()
                            self.failed_proxies.clear()
                            self.current_proxy_index = 0
                            
                            self.logger.info(f"✅ Fetched {len(working_proxies)} working proxies")
                            return True
                        else:
                            self.logger.warning("⚠️ No working proxies found in API response")
                            return False
                    else:
                        self.logger.error(f"❌ Failed to fetch proxies: HTTP {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"❌ Error fetching proxies: {e}")
            return False
    
    async def get_proxy(self) -> Optional[str]:
        """Get next available proxy
        
        Returns:
            Proxy URL string or None if no proxies available
        """
        # Check if we need to refresh proxies
        if (not self.proxies or 
            not self.last_fetch_time or 
            datetime.now() - self.last_fetch_time > self.fetch_interval):
            
            await self.fetch_proxies()
        
        # If still no proxies, return None
        if not self.proxies:
            return None
        
        # Find next working proxy
        attempts = 0
        while attempts < len(self.proxies):
            proxy = self.proxies[self.current_proxy_index]
            proxy_key = f"{proxy['ip']}:{proxy['port']}"
            
            # Skip failed proxies
            if proxy_key not in self.failed_proxies:
                return proxy['url']
            
            # Move to next proxy
            self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
            attempts += 1
        
        # All proxies failed, clear failed list and try again
        self.failed_proxies.clear()
        if self.proxies:
            return self.proxies[0]['url']
        
        return None
    
    def mark_proxy_failed(self, proxy_url: str) -> None:
        """Mark a proxy as failed
        
        Args:
            proxy_url: The proxy URL that failed
        """
        for proxy in self.proxies:
            if proxy['url'] == proxy_url:
                proxy_key = f"{proxy['ip']}:{proxy['port']}"
                self.failed_proxies.add(proxy_key)
                self.logger.warning(f"⚠️ Marked proxy as failed: {proxy_key}")
                break
    
    def get_random_proxy(self) -> Optional[str]:
        """Get a random proxy from available list
        
        Returns:
            Random proxy URL or None if no proxies available
        """
        if not self.proxies:
            return None
        
        # Filter out failed proxies
        working_proxies = []
        for proxy in self.proxies:
            proxy_key = f"{proxy['ip']}:{proxy['port']}"
            if proxy_key not in self.failed_proxies:
                working_proxies.append(proxy)
        
        if working_proxies:
            return random.choice(working_proxies)['url']
        
        return None
    
    def get_proxy_stats(self) -> Dict:
        """Get proxy statistics
        
        Returns:
            Dictionary with proxy statistics
        """
        total_proxies = len(self.proxies)
        failed_proxies = len(self.failed_proxies)
        working_proxies = total_proxies - failed_proxies
        
        return {
            'total_proxies': total_proxies,
            'working_proxies': working_proxies,
            'failed_proxies': failed_proxies,
            'last_fetch': self.last_fetch_time.isoformat() if self.last_fetch_time else None
        }