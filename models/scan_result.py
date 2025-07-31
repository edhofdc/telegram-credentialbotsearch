#!/usr/bin/env python3
"""
Scan Result Model
Handles scan result data structure and operations
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class CredentialMatch:
    """Data class for credential matches"""
    type: str
    value: str
    context: str
    source: str
    line_number: Optional[int] = None
    confidence: str = "medium"


@dataclass
class EndpointMatch:
    """Data class for endpoint matches"""
    url: str
    method: str
    source: str
    line_number: Optional[int] = None
    parameters: Optional[List[str]] = None

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []


@dataclass
class ScanResult:
    """Main scan result data structure"""
    target_url: str
    scan_time: datetime
    credentials: List[CredentialMatch]
    endpoints: List[EndpointMatch]
    scan_duration: float = 0.0
    status: str = "completed"
    error_message: Optional[str] = None

    def __post_init__(self):
        if not self.credentials:
            self.credentials = []
        if not self.endpoints:
            self.endpoints = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert scan result to dictionary"""
        return {
            'target_url': self.target_url,
            'scan_time': self.scan_time.isoformat(),
            'credentials': [{
                'type': cred.type,
                'value': cred.value,
                'context': cred.context,
                'source': cred.source,
                'line_number': cred.line_number,
                'confidence': cred.confidence
            } for cred in self.credentials],
            'endpoints': [{
                'url': ep.url,
                'method': ep.method,
                'source': ep.source,
                'line_number': ep.line_number,
                'parameters': ep.parameters
            } for ep in self.endpoints],
            'scan_duration': self.scan_duration,
            'status': self.status,
            'error_message': self.error_message
        }

    def has_findings(self) -> bool:
        """Check if scan has any findings"""
        return len(self.credentials) > 0 or len(self.endpoints) > 0

    def get_summary(self) -> Dict[str, int]:
        """Get summary statistics"""
        return {
            'total_credentials': len(self.credentials),
            'total_endpoints': len(self.endpoints),
            'high_risk_credentials': len([c for c in self.credentials if c.confidence == 'high']),
            'medium_risk_credentials': len([c for c in self.credentials if c.confidence == 'medium']),
            'low_risk_credentials': len([c for c in self.credentials if c.confidence == 'low'])
        }