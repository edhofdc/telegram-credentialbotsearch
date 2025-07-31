#!/usr/bin/env python3
"""
Scanner Service
Handles website scanning operations and credential detection
"""

import re
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import time
import logging

from models.scan_result import ScanResult, CredentialMatch, EndpointMatch
from services.proxy_service import ProxyService


class ScannerService:
    """Service class for website scanning operations"""
    
    def __init__(self, max_file_size: int = 5 * 1024 * 1024, request_timeout: int = 30, use_proxy: bool = True, progress_callback=None):
        """Initialize scanner service
        
        Args:
            max_file_size: Maximum file size to download in bytes
            request_timeout: Request timeout in seconds
            use_proxy: Whether to use proxy rotation for requests
            progress_callback: Callback function for progress updates
        """
        self.max_file_size = max_file_size
        self.request_timeout = request_timeout
        self.use_proxy = use_proxy
        self.progress_callback = progress_callback
        self.proxy_service = ProxyService() if use_proxy else None
        self.logger = logging.getLogger(__name__)
        
        # Credential patterns for detection
        self.credential_patterns = {
            'apiKey': [
                r'API_KEY["\s]*:["\s]*([a-zA-Z0-9_-]{20,})',
                r'API_KEY["\s]*:["\s]*"([a-zA-Z0-9_-]{20,})',
                r'api[_-]?key["\s]*[:=]["\s]*([a-zA-Z0-9_-]{20,})',
                r'apikey["\s]*[:=]["\s]*([a-zA-Z0-9_-]{20,})',
                r'key["\s]*[:=]["\s]*([a-zA-Z0-9_-]{32,})',
                r'"API_KEY"\s*:\s*"([^"]+)"',
                r'API_KEY\s*:\s*"([^"]+)"'
            ],
            'googleApi': [
                r'googleApi["\s]*:["\s]*(AIza[0-9A-Za-z_-]{35})',
                r'google[_-]?api["\s]*[:=]["\s]*(AIza[0-9A-Za-z_-]{35})',
                r'googleApi\s*:\s*(AIza[0-9A-Za-z_-]{35})',
                r'"googleApi"\s*:\s*"(AIza[0-9A-Za-z_-]{35})"'
            ],
            'secret_key': [
                r'secret[_-]?key["\s]*[:=]["\s]*([a-zA-Z0-9_-]{20,})',
                r'secretkey["\s]*[:=]["\s]*([a-zA-Z0-9_-]{20,})'
            ],
            'access_token': [
                r'access[_-]?token["\s]*[:=]["\s]*([a-zA-Z0-9_-]{20,})',
                r'accesstoken["\s]*[:=]["\s]*([a-zA-Z0-9_-]{20,})'
            ],
            'firebase_key': [
                r'AIza[0-9A-Za-z_-]{35}'
            ],
            'awsKey': [
                r'AKiA[0-9A-Za-z]{16}',
                r'AKIA[0-9A-Z]{16}',
                r'"awsKey"\s*:\s*"(AKiA[0-9A-Za-z]{16})"',
                r'awsKey\s*:\s*(AKiA[0-9A-Za-z]{16})',
                r'aws[_-]?key["\s]*[:=]["\s]*(AKiA[0-9A-Za-z]{16})',
                r'(AKiA[0-9A-Za-z]{16})'
            ],
            'github_token': [
                r'ghp_[a-zA-Z0-9]{36}',
                r'github_pat_[a-zA-Z0-9_]{82}'
            ],
            'jwt_token': [
                r'eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*'
            ]
        }
        
        # Endpoint patterns
        self.endpoint_patterns = [
            r'["\']\s*(/api/[^"\s]+)["\']',
            r'["\']\s*(/v\d+/[^"\s]+)["\']',
            r'["\']\s*(https?://[^"\s]+/api/[^"\s]+)["\']',
            r'fetch\s*\(["\']([^"\s]+)["\']',
            r'axios\.[get|post|put|delete]+\s*\(["\']([^"\s]+)["\']',
            r'\$\.ajax\s*\([^{]*url\s*:\s*["\']([^"\s]+)["\']'
        ]
    
    def _escape_markdown_v2(self, text: str) -> str:
        """
        Escape special characters for MarkdownV2 using regex
        
        Args:
            text: Text to escape
            
        Returns:
            Escaped text safe for MarkdownV2
        """
        # Escape all MarkdownV2 special characters
        special_chars = r'([_*\[\]()~`>#+=|{}.!-])'
        return re.sub(special_chars, r'\\\1', text)
    
    def normalize_url(self, url: str) -> str:
        """Normalize URL by adding protocol if missing
        
        Args:
            url: Input URL
            
        Returns:
            Normalized URL with protocol
        """
        if not url.startswith(('http://', 'https://')):
            return f'https://{url}'
        return url
    
    def is_valid_url(self, url: str) -> bool:
        """Validate URL format
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid, False otherwise
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    async def _create_session_without_proxy(self) -> aiohttp.ClientSession:
        """Create aiohttp session for direct connection without proxy
        
        Returns:
            ClientSession: HTTP session for direct connection
        """
        timeout = aiohttp.ClientTimeout(total=self.request_timeout)
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
        session = aiohttp.ClientSession(
            timeout=timeout, 
            connector=connector,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        
        return session
    
    async def _make_request_with_retry(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Make HTTP request with retry logic without proxy
        
        Args:
            url: URL to request
            max_retries: Maximum number of retries
            
        Returns:
            Response text content or None if failed
        """
        for attempt in range(max_retries):
            session = None
            try:
                session = await self._create_session_without_proxy()
                
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.request_timeout)) as response:
                    if response.status == 200:
                        content = await response.text()
                        self.logger.info(f"Successfully fetched {url} on attempt {attempt + 1}")
                        return content
                    elif response.status in [403, 429, 503]:  # Rate limiting or blocking
                        self.logger.warning(f"Blocked (HTTP {response.status}) on attempt {attempt + 1} for {url}")
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        self.logger.warning(f"HTTP {response.status} for {url}")
                        return None
                        
            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout on attempt {attempt + 1} for {url}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
            except Exception as e:
                self.logger.warning(f"Error on attempt {attempt + 1} for {url}: {str(e)}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
            finally:
                if session and not session.closed:
                    await session.close()
                    
        self.logger.error(f"Failed to fetch {url} after {max_retries} attempts")
        return None
    
    async def _send_progress_update(self, message: str) -> None:
        """Send progress update via callback if available
        
        Args:
            message: Progress message to send
        """
        if self.progress_callback:
            try:
                await self.progress_callback(message)
            except Exception as e:
                self.logger.warning(f"Failed to send progress update: {e}")
    
    async def scan_website(self, url: str) -> ScanResult:
        """Scan website for credentials and endpoints with interactive progress
        
        Args:
            url: Target URL to scan
            
        Returns:
            ScanResult object containing findings
        """
        start_time = time.time()
        normalized_url = self.normalize_url(url)
        
        # Send initial progress update
        await self._send_progress_update(f"🎯 *Starting website scan:* `{self._escape_markdown_v2(normalized_url)}`")
        
        scan_result = ScanResult(
            target_url=normalized_url,
            scan_time=datetime.now(),
            credentials=[],
            endpoints=[]
        )
        
        try:
            # Skip proxy initialization - using direct connection
            await self._send_progress_update("🔄 *Menggunakan koneksi langsung tanpa proxy\.\.\.\*")
            self.logger.info("🔄 Using direct connection without proxy")
            
            # Scan main page
            await self._send_progress_update("📄 *Scanning main page\.\.\.*")
            await self._scan_page_with_retry(normalized_url, scan_result)
            
            # Find and scan JavaScript files
            await self._send_progress_update("🔍 *Searching for JavaScript files\.\.\.*")
            await self._find_and_scan_js_files_with_retry(normalized_url, scan_result)
                
            scan_result.status = "completed"
            
            # Send completion summary
            total_credentials = len(scan_result.credentials)
            total_endpoints = len(scan_result.endpoints)
            duration = time.time() - start_time
            
            await self._send_progress_update(
                f"✅ *Scan completed\!*\n"
                f"🔑 Credentials found: *{total_credentials}*\n"
                f"🌐 Endpoints found: *{total_endpoints}*\n"
                f"⏱️ Duration: *{duration:.1f} seconds*"
            )
            
        except (GeneratorExit, asyncio.CancelledError):
            # Handle graceful shutdown
            scan_result.status = "cancelled"
            scan_result.error_message = "Scan cancelled due to shutdown"
            await self._send_progress_update("❌ *Scan cancelled*")
            raise  # Re-raise to allow proper cleanup
        except Exception as e:
            scan_result.status = "error"
            scan_result.error_message = str(e)
            await self._send_progress_update(self._format_error_message(str(e)))
            self.logger.error(f"❌ Scan failed: {e}")
        
        scan_result.scan_duration = time.time() - start_time
        return scan_result
    
    async def _scan_page_with_retry(self, url: str, scan_result: ScanResult) -> None:
        """Scan a single page with retry logic
        
        Args:
            url: Page URL to scan
            scan_result: Result object to update
        """
        try:
            content = await self._make_request_with_retry(url)
            if content:
                self._analyze_content(content, url, scan_result)
                self.logger.info(f"Successfully scanned page: {url}")
        except Exception as e:
            self.logger.warning(f"Failed to scan page {url}: {str(e)}")
    
    async def _scan_page(self, session: aiohttp.ClientSession, url: str, scan_result: ScanResult) -> None:
        """Scan a single page for credentials and endpoints
        
        Args:
            session: HTTP session
            url: Page URL to scan
            scan_result: Result object to update
        """
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    self._analyze_content(content, url, scan_result)
        except Exception:
            pass  # Continue scanning other resources
    
    async def _find_and_scan_js_files_with_retry(self, base_url: str, scan_result: ScanResult) -> None:
        """Find and scan JavaScript files with retry logic
        
        Args:
            base_url: Base URL of the website
            scan_result: Result object to update
        """
        try:
            content = await self._make_request_with_retry(base_url)
            if content:
                soup = BeautifulSoup(content, 'html.parser')
                
                # Find script tags with src attribute
                script_tags = soup.find_all('script', src=True)
                
                # Send progress update with JS files count
                await self._send_progress_update(f"📄 *JS files found:* {len(script_tags)} files")
                
                # Limit concurrent requests
                semaphore = asyncio.Semaphore(3)  # Reduced for stability
                tasks = []
                
                if script_tags:
                    await self._send_progress_update("🔍 *Searching for credentials\.\.\.*")
                    
                    for script in script_tags:
                        script_url = urljoin(base_url, script['src'])
                        task = self._scan_js_file_with_retry_semaphore(semaphore, script_url, scan_result)
                        tasks.append(task)
                    
                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)
                        self.logger.info(f"Scanned {len(script_tags)} JavaScript files")
                else:
                    await self._send_progress_update("ℹ️ *No JavaScript files found*")
                    
        except Exception as e:
            self.logger.warning(f"Failed to find JS files from {base_url}: {str(e)}")
    
    async def _find_and_scan_js_files(self, session: aiohttp.ClientSession, base_url: str, scan_result: ScanResult) -> None:
        """Find and scan JavaScript files from the main page
        
        Args:
            session: HTTP session
            base_url: Base URL of the website
            scan_result: Result object to update
        """
        try:
            async with session.get(base_url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Find script tags with src attribute
                    script_tags = soup.find_all('script', src=True)
                    
                    # Limit concurrent requests
                    semaphore = asyncio.Semaphore(5)
                    tasks = []
                    
                    for script in script_tags:
                        script_url = urljoin(base_url, script['src'])
                        task = self._scan_js_file_with_semaphore(semaphore, session, script_url, scan_result)
                        tasks.append(task)
                    
                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)
                        
        except Exception:
            pass  # Continue with main page scan
    
    async def _scan_js_file_with_retry_semaphore(self, semaphore: asyncio.Semaphore, script_url: str, scan_result: ScanResult) -> None:
        """Scan JavaScript file with retry logic and semaphore for concurrency control
        
        Args:
            semaphore: Semaphore for concurrency control
            script_url: JavaScript file URL
            scan_result: Result object to update
        """
        async with semaphore:
            await self._scan_js_file_with_retry(script_url, scan_result)
    
    async def _scan_js_file_with_retry(self, script_url: str, scan_result: ScanResult) -> None:
        """Scan JavaScript file with retry logic
        
        Args:
            script_url: JavaScript file URL
            scan_result: Result object to update
        """
        try:
            content = await self._make_request_with_retry(script_url)
            if content:
                # Check content length
                if len(content) > self.max_file_size:
                    self.logger.warning(f"JavaScript file too large: {script_url}")
                    return
                
                self._analyze_content(content, script_url, scan_result)
                self.logger.info(f"Successfully scanned JS file: {script_url}")
        except Exception as e:
            self.logger.warning(f"Failed to scan JS file {script_url}: {str(e)}")
    
    async def _scan_js_file_with_semaphore(self, semaphore: asyncio.Semaphore, session: aiohttp.ClientSession, 
                                          script_url: str, scan_result: ScanResult) -> None:
        """Scan JavaScript file with semaphore for concurrency control
        
        Args:
            semaphore: Semaphore for concurrency control
            session: HTTP session
            script_url: JavaScript file URL
            scan_result: Result object to update
        """
        async with semaphore:
            await self._scan_js_file(session, script_url, scan_result)
    
    async def _scan_js_file(self, session: aiohttp.ClientSession, script_url: str, scan_result: ScanResult) -> None:
        """Scan individual JavaScript file
        
        Args:
            session: HTTP session
            script_url: JavaScript file URL
            scan_result: Result object to update
        """
        try:
            async with session.get(script_url) as response:
                if response.status == 200:
                    # Check content length
                    content_length = response.headers.get('content-length')
                    if content_length and int(content_length) > self.max_file_size:
                        return
                    
                    content = await response.text()
                    if len(content.encode('utf-8')) <= self.max_file_size:
                        self._analyze_content(content, script_url, scan_result)
                        
        except Exception:
            pass  # Continue scanning other files
    
    def _analyze_content(self, content: str, source: str, scan_result: ScanResult) -> None:
        """Analyze content for credentials and endpoints
        
        Args:
            content: Content to analyze
            source: Source URL/file
            scan_result: Result object to update
        """
        # Find credentials
        self._find_credentials(content, source, scan_result)
        
        # Find endpoints
        self._find_endpoints(content, source, scan_result)
    
    def _find_credentials(self, content: str, source: str, scan_result: ScanResult) -> None:
        """Find credentials in content
        
        Args:
            content: Content to search
            source: Source URL/file
            scan_result: Result object to update
        """
        lines = content.split('\n')
        
        for cred_type, patterns in self.credential_patterns.items():
            for pattern in patterns:
                for line_num, line in enumerate(lines, 1):
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        credential = CredentialMatch(
                            type=cred_type,
                            value=match.group(1) if match.groups() else match.group(0),
                            context=self._get_context(content, match.start(), 50),
                            source=self._get_short_source(source),
                            line_number=line_num,
                            confidence=self._get_confidence_level(cred_type, match.group(0))
                        )
                        scan_result.credentials.append(credential)
    
    def _find_endpoints(self, content: str, source: str, scan_result: ScanResult) -> None:
        """Find API endpoints in content
        
        Args:
            content: Content to search
            source: Source URL/file
            scan_result: Result object to update
        """
        lines = content.split('\n')
        
        for pattern in self.endpoint_patterns:
            for line_num, line in enumerate(lines, 1):
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    endpoint_url = match.group(1)
                    if self._is_valid_endpoint(endpoint_url):
                        endpoint = EndpointMatch(
                            url=endpoint_url,
                            method=self._detect_http_method(line),
                            source=self._get_short_source(source),
                            line_number=line_num
                        )
                        scan_result.endpoints.append(endpoint)
    
    def _get_context(self, content: str, index: int, context_length: int = 50) -> str:
        """Get context around a match
        
        Args:
            content: Full content
            index: Match index
            context_length: Length of context to extract
            
        Returns:
            Context string
        """
        start = max(0, index - context_length)
        end = min(len(content), index + context_length)
        return content[start:end].strip()
    
    def _get_short_source(self, source: str) -> str:
        """Get shortened source name
        
        Args:
            source: Full source URL
            
        Returns:
            Shortened source name
        """
        if len(source) > 50:
            return f"...{source[-47:]}"
        return source
    
    def _get_confidence_level(self, cred_type: str, value: str) -> str:
        """Determine confidence level for credential match
        
        Args:
            cred_type: Type of credential
            value: Credential value
            
        Returns:
            Confidence level (high/medium/low)
        """
        if cred_type in ['firebase_key', 'aws_key', 'github_token']:
            return 'high'
        elif len(value) > 40:
            return 'high'
        elif len(value) > 25:
            return 'medium'
        else:
            return 'low'
    
    def _is_valid_endpoint(self, endpoint: str) -> bool:
        """Check if endpoint is valid
        
        Args:
            endpoint: Endpoint URL
            
        Returns:
            True if valid endpoint
        """
        # Filter out common false positives
        false_positives = [
            '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg',
            '.ico', '.woff', '.ttf', '.eot', '.map'
        ]
        
        endpoint_lower = endpoint.lower()
        return not any(fp in endpoint_lower for fp in false_positives)
    
    def _detect_http_method(self, line: str) -> str:
        """Detect HTTP method from line context
        
        Args:
            line: Line containing endpoint
            
        Returns:
            HTTP method (GET/POST/PUT/DELETE)
        """
        line_lower = line.lower()
        
        if 'post' in line_lower:
            return 'POST'
        elif 'put' in line_lower:
            return 'PUT'
        elif 'delete' in line_lower:
            return 'DELETE'
        else:
            return 'GET'

    # Removed duplicate _escape_markdown function - using _escape_markdown_v2 instead
    
    def _format_error_message(self, error_msg: str) -> str:
        """
        Format error message for MarkdownV2 with proper escaping
        
        Args:
            error_msg: Raw error message
            
        Returns:
            Properly escaped error message for MarkdownV2
        """
        # Escape the error message for MarkdownV2
        escaped_msg = self._escape_markdown_v2(str(error_msg))
        return f"❌ *Error during scan:* `{escaped_msg}`"