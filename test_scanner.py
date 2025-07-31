#!/usr/bin/env python3
import asyncio
from services.scanner_service import ScannerService

async def test_multiple_websites():
    """Test scanner with multiple websites"""
    scanner = ScannerService()
    
    websites = [
        'https://example.com',
        'https://httpbin.org',
        'https://jsonplaceholder.typicode.com',
        'https://github.com'
    ]
    
    for url in websites:
        print(f"\n🔍 Testing scanner with {url}...")
        
        try:
            result = await scanner.scan_website(url)
            
            print(f"📊 Results for {url}:")
            print(f"• Credentials: {len(result.credentials)}")
            print(f"• Endpoints: {len(result.endpoints)}")
            print(f"• Status: {result.status}")
            print(f"• Duration: {result.scan_duration:.2f}s")
            
            if result.error_message:
                print(f"• Error: {result.error_message}")
            
            if result.credentials:
                print(f"🔐 Credentials found:")
                for i, cred in enumerate(result.credentials[:5], 1):
                    print(f"  {i}. {cred.type}: {cred.value[:50]}...")
                    print(f"     Source: {cred.source}")
                    
        except Exception as e:
            print(f"❌ Error testing {url}: {e}")
        
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_multiple_websites())