#!/usr/bin/env python3
"""
PDF Report Service
Handles PDF report generation for scan results
"""

import os
from datetime import datetime
from typing import Optional
from io import BytesIO

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.platypus.tableofcontents import TableOfContents
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
except ImportError:
    print("ReportLab not installed. Install with: pip install reportlab")
    raise

from models.scan_result import ScanResult


class PDFReportService:
    """Service for generating PDF reports from scan results"""
    
    def __init__(self):
        """Initialize PDF report service"""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self) -> None:
        """Setup custom paragraph styles for the report"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            textColor=colors.darkred
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=15,
            spaceBefore=20,
            textColor=colors.darkgreen
        ))
        
        # Warning style
        self.styles.add(ParagraphStyle(
            name='Warning',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.red,
            backColor=colors.lightgrey,
            borderColor=colors.red,
            borderWidth=1,
            leftIndent=10,
            rightIndent=10,
            spaceAfter=10
        ))
    
    def generate_report(self, scan_result: ScanResult, output_path: Optional[str] = None) -> str:
        """Generate PDF report from scan result
        
        Args:
            scan_result: Scan result data
            output_path: Optional output file path
            
        Returns:
            Path to generated PDF file
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recon_report_{timestamp}.pdf"
            output_path = os.path.join(os.getcwd(), "reports", filename)
        
        # Create reports directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build story (content)
        story = []
        
        # Add title page
        self._add_title_page(story, scan_result)
        
        # Add executive summary
        self._add_executive_summary(story, scan_result)
        
        # Add scan details
        self._add_scan_details(story, scan_result)
        
        # Add findings
        if scan_result.has_findings():
            self._add_findings_section(story, scan_result)
        else:
            self._add_no_findings_section(story)
        
        # Add recommendations
        self._add_recommendations(story, scan_result)
        
        # Add appendix
        self._add_appendix(story, scan_result)
        
        # Build PDF
        doc.build(story)
        
        return output_path
    
    def _add_title_page(self, story: list, scan_result: ScanResult) -> None:
        """Add title page to the report
        
        Args:
            story: PDF story elements
            scan_result: Scan result data
        """
        # Main title
        title = Paragraph("Security Reconnaissance Report", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 0.5*inch))
        
        # Target information
        target_info = f"<b>Target:</b> {scan_result.target_url}"
        story.append(Paragraph(target_info, self.styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Scan information
        scan_info = f"<b>Scan Date:</b> {scan_result.scan_time.strftime('%Y-%m-%d %H:%M:%S')}"
        story.append(Paragraph(scan_info, self.styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        duration_info = f"<b>Scan Duration:</b> {scan_result.scan_duration:.2f} seconds"
        story.append(Paragraph(duration_info, self.styles['Normal']))
        story.append(Spacer(1, 0.5*inch))
        
        # Warning notice
        warning_text = (
            "<b>CONFIDENTIAL SECURITY REPORT</b><br/><br/>"
            "This report contains sensitive security information. "
            "Handle with appropriate care and distribute only to authorized personnel."
        )
        story.append(Paragraph(warning_text, self.styles['Warning']))
        
        # Page break
        story.append(Spacer(1, 2*inch))
    
    def _add_executive_summary(self, story: list, scan_result: ScanResult) -> None:
        """Add executive summary section
        
        Args:
            story: PDF story elements
            scan_result: Scan result data
        """
        story.append(Paragraph("Executive Summary", self.styles['CustomSubtitle']))
        
        summary_stats = scan_result.get_summary()
        
        if scan_result.has_findings():
            summary_text = (
                f"The security reconnaissance scan of {scan_result.target_url} "
                f"identified {summary_stats['total_credentials']} potential credential exposures "
                f"and {summary_stats['total_endpoints']} API endpoints. "
            )
            
            if summary_stats['high_risk_credentials'] > 0:
                summary_text += (
                    f"<b>Critical:</b> {summary_stats['high_risk_credentials']} high-risk "
                    "credentials were detected that require immediate attention."
                )
            else:
                summary_text += "No high-risk credentials were detected."
        else:
            summary_text = (
                f"The security reconnaissance scan of {scan_result.target_url} "
                "completed successfully with no credential exposures or suspicious "
                "API endpoints detected. This indicates good security practices "
                "regarding credential management."
            )
        
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
    
    def _add_scan_details(self, story: list, scan_result: ScanResult) -> None:
        """Add scan details section
        
        Args:
            story: PDF story elements
            scan_result: Scan result data
        """
        story.append(Paragraph("Scan Details", self.styles['CustomSubtitle']))
        
        # Create details table
        details_data = [
            ['Parameter', 'Value'],
            ['Target URL', scan_result.target_url],
            ['Scan Status', scan_result.status.title()],
            ['Scan Duration', f"{scan_result.scan_duration:.2f} seconds"],
            ['Scan Timestamp', scan_result.scan_time.strftime('%Y-%m-%d %H:%M:%S UTC')]
        ]
        
        if scan_result.error_message:
            details_data.append(['Error Message', scan_result.error_message])
        
        details_table = Table(details_data, colWidths=[2*inch, 4*inch])
        details_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(details_table)
        story.append(Spacer(1, 0.3*inch))
    
    def _add_findings_section(self, story: list, scan_result: ScanResult) -> None:
        """Add findings section with credentials and endpoints
        
        Args:
            story: PDF story elements
            scan_result: Scan result data
        """
        story.append(Paragraph("Security Findings", self.styles['CustomSubtitle']))
        
        # Credentials section
        if scan_result.credentials:
            story.append(Paragraph("Credential Exposures", self.styles['SectionHeader']))
            
            cred_data = [['Type', 'Value', 'Source', 'Risk Level']]
            
            for cred in scan_result.credentials:
                # Display full values without masking
                risk_color = self._get_risk_color(cred.confidence)
                
                cred_data.append([
                    cred.type.replace('_', ' ').title(),
                    cred.value,
                    cred.source,
                    cred.confidence.title()
                ])
            
            cred_table = Table(cred_data, colWidths=[1.5*inch, 2*inch, 2*inch, 1*inch])
            cred_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(cred_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Endpoints section
        if scan_result.endpoints:
            story.append(Paragraph("API Endpoints", self.styles['SectionHeader']))
            
            endpoint_data = [['Method', 'URL', 'Source']]
            
            for endpoint in scan_result.endpoints:
                endpoint_data.append([
                    endpoint.method,
                    endpoint.url,
                    endpoint.source
                ])
            
            endpoint_table = Table(endpoint_data, colWidths=[1*inch, 3.5*inch, 2*inch])
            endpoint_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(endpoint_table)
            story.append(Spacer(1, 0.3*inch))
    
    def _add_no_findings_section(self, story: list) -> None:
        """Add section for when no findings are detected
        
        Args:
            story: PDF story elements
        """
        story.append(Paragraph("Security Findings", self.styles['CustomSubtitle']))
        
        no_findings_text = (
            "<b>No Security Issues Detected</b><br/><br/>"
            "The reconnaissance scan did not identify any exposed credentials "
            "or suspicious API endpoints. This suggests that the target website "
            "follows good security practices regarding credential management "
            "and API exposure."
        )
        
        story.append(Paragraph(no_findings_text, self.styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
    
    def _add_recommendations(self, story: list, scan_result: ScanResult) -> None:
        """Add recommendations section
        
        Args:
            story: PDF story elements
            scan_result: Scan result data
        """
        story.append(Paragraph("Recommendations", self.styles['CustomSubtitle']))
        
        if scan_result.has_findings():
            recommendations = [
                "1. <b>Immediate Action Required:</b> Remove all exposed credentials from public-facing code and files.",
                "2. <b>Credential Management:</b> Implement proper environment variable management for sensitive data.",
                "3. <b>Code Review:</b> Establish code review processes to prevent credential exposure.",
                "4. <b>Monitoring:</b> Implement automated scanning in CI/CD pipelines.",
                "5. <b>Access Control:</b> Review and restrict access to sensitive API endpoints.",
                "6. <b>Rotation:</b> Rotate all exposed credentials immediately."
            ]
        else:
            recommendations = [
                "1. <b>Maintain Current Practices:</b> Continue following secure coding practices.",
                "2. <b>Regular Scanning:</b> Perform periodic security scans to maintain security posture.",
                "3. <b>Team Training:</b> Ensure development team stays updated on security best practices.",
                "4. <b>Monitoring:</b> Consider implementing automated security scanning in development workflow."
            ]
        
        for rec in recommendations:
            story.append(Paragraph(rec, self.styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        
        story.append(Spacer(1, 0.3*inch))
    
    def _add_appendix(self, story: list, scan_result: ScanResult) -> None:
        """Add appendix with technical details
        
        Args:
            story: PDF story elements
            scan_result: Scan result data
        """
        story.append(Paragraph("Appendix", self.styles['CustomSubtitle']))
        
        # Methodology
        story.append(Paragraph("Scanning Methodology", self.styles['SectionHeader']))
        
        methodology_text = (
            "This reconnaissance scan was performed using automated tools that analyze "
            "web pages and JavaScript files for exposed credentials and API endpoints. "
            "The scan includes pattern matching for common credential types including "
            "API keys, access tokens, and database credentials."
        )
        
        story.append(Paragraph(methodology_text, self.styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Disclaimer
        story.append(Paragraph("Disclaimer", self.styles['SectionHeader']))
        
        disclaimer_text = (
            "This report is generated by automated scanning tools and may contain "
            "false positives. Manual verification of findings is recommended. "
            "This scan is intended for authorized security testing purposes only."
        )
        
        story.append(Paragraph(disclaimer_text, self.styles['Normal']))
    

    
    def _get_risk_color(self, confidence: str) -> str:
        """Get color for risk level
        
        Args:
            confidence: Confidence level
            
        Returns:
            Color name
        """
        color_map = {
            'high': 'red',
            'medium': 'orange',
            'low': 'yellow'
        }
        return color_map.get(confidence.lower(), 'black')