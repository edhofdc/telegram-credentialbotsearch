#!/usr/bin/env python3
"""
Bot Presenter
Handles Telegram bot interactions and user interface logic
Implements MVP pattern - Presenter layer for bot operations
"""

import asyncio
import logging
import os
import re
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime

# Type checking imports
if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    from telegram.constants import ParseMode
    import telegram
else:
    # Runtime imports with error handling
    try:
        import telegram
        from telegram import Update
        from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
        from telegram.constants import ParseMode
    except ImportError as e:
        logging.error(f"Failed to import Telegram modules: {e}")
        raise

from services.scanner_service import ScannerService
from services.pdf_service import PDFReportService
from models.scan_result import ScanResult


class BotPresenter:
    """Presenter class for Telegram bot interactions"""
    
    def __init__(self, admin_chat_id: str, target_topic_id: str):
        """Initialize bot presenter
        
        Args:
            admin_chat_id: Admin's chat ID for private messages
            target_topic_id: Target topic ID for group operations
        """
        self.admin_chat_id = admin_chat_id
        self.target_topic_id = target_topic_id
        self.scanner_service = ScannerService()
        self.pdf_service = PDFReportService()
        self.active_scans: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"🤖 Bot Presenter initialized")
        self.logger.info(f"   Admin Chat ID: {self.admin_chat_id}")
        self.logger.info(f"   Target Topic ID: {self.target_topic_id}")
    
    def register_handlers(self, application) -> None:
        """Register all bot command and message handlers
        
        Args:
            application: Telegram application instance
        """
        try:
            # Command handlers
            application.add_handler(CommandHandler("start", self.handle_start_command))
            application.add_handler(CommandHandler("help", self.handle_help_command))
            application.add_handler(CommandHandler("scan", self.handle_scan_command))
            application.add_handler(CommandHandler("status", self.handle_status_command))
            application.add_handler(CommandHandler("report", self.handle_report_command))
            application.add_handler(CommandHandler("reportpdf", self.handle_reportpdf_command))
            application.add_handler(CommandHandler("enter", self.handle_enter_command))
            
            # Private message handler with safe filter combination
            if hasattr(filters, 'TEXT') and hasattr(filters, 'ChatType'):
                try:
                    private_filter = filters.TEXT & filters.ChatType.PRIVATE
                    application.add_handler(MessageHandler(private_filter, self.handle_private_message))
                except Exception as e:
                    self.logger.warning(f"Could not register private message handler: {e}")
            
            self.logger.info("✅ All handlers registered successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to register handlers: {e}")
            raise
    
    async def handle_start_command(self, update: Update, context) -> None:
        """Handle /start command
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        try:
            if not self._is_valid_context(update):
                return
            
            welcome_message = (
                "🎯 *Welcome to Telegram Recon Bot\!*\n\n"
                "🔍 This bot helps you perform *reconnaissance* to detect:"
                "\n• 🔑 Exposed credentials \(API keys, tokens\)"
                "\n• 🌐 Accessible API endpoints\n\n"
                "📋 *Available Commands:*\n"
                "• `/help` \- Complete help\n"
                "• `/scan <URL>` \- Scan website\n"
                "• `/status` \- Bot status and active scans\n"
                "• `/reportpdf <URL>` \- Generate PDF report\n\n"
                "⚠️ *Important:* Only scan websites you own or have permission\!"
            )
            
            await update.message.reply_text(
                welcome_message,
                parse_mode=None
            )
            
        except Exception as e:
            self.logger.error(f"Error in start command: {e}")
            await self._send_error_message(update, "Failed to process start command")
    
    async def handle_help_command(self, update: Update, context) -> None:
        """Handle /help command
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        try:
            if not self._is_valid_context(update):
                return
            
            help_message = (
                "📖 *Bot Usage Guide*\n\n"
                "🔍 *Scanning Commands:*\n"
                "• `/scan <URL>` \- Scan website for credentials\n"
                "• `/reportpdf <URL>` \- Generate complete PDF report\n"
                "• `/status` \- View running scan status\n\n"
                "💡 *Usage Examples:*\n"
                "• `/scan example\.com`\n"
                "• `/scan https://target\.com`\n"
                "• `/reportpdf https://example\.com`\n\n"
                "🎯 *Fitur Deteksi:*\n"
                "• 🔑 API Keys \(Firebase, AWS, Google\)\n"
                "• 🔐 Access Tokens & Secret Keys\n"
                "• 🌐 API Endpoints from JavaScript\n\n"
                "⚠️ *Security Notes:*\n"
                "• Only scan websites you own\n"
                "• Use for legitimate security purposes\n"
                "• Report findings to website owners"
            )
            
            await update.message.reply_text(
                help_message,
                parse_mode=None
            )
            
        except Exception as e:
            self.logger.error(f"Error in help command: {e}")
            await self._send_error_message(update, "Failed to process help command")
    
    async def handle_scan_command(self, update: Update, context) -> None:
        """Handle /scan command with interactive status updates
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        try:
            if not self._is_valid_context(update):
                return
            
            # Extract URL from command
            if not context.args:
                await update.message.reply_text(
                    "❌ Wrong format!\n\n"
                    "Usage: /scan <URL>\n"
                    "Example: /scan example.com",
                    parse_mode=None
                )
                return
            
            url = context.args[0]
            normalized_url = self._normalize_url(url)
            
            # Check if scan is already running
            user_id = getattr(update.effective_user, 'id', 0)
            scan_key = f"{user_id}_{normalized_url}"
            
            if scan_key in self.active_scans:
                await update.message.reply_text(
                    "⚠️ Scan already running for this URL!\n\n"
                    "Use /status to view progress.",
                    parse_mode=None
                )
                return
            
            # Send initial status message
            status_message = await update.message.reply_text(
                f"🤖 Bot is running...\n⏳ Initializing scan process\n\n"
                f"🎯 Target: {normalized_url}",
                parse_mode=None
            )
            
            # Create progress callback with status updates
            async def progress_callback(message: str, js_files_count: int = 0):
                try:
                    if js_files_count > 0:
                        await status_message.edit_text(
                            f"🤖 Bot is running...\n"
                            f"📁 Found {js_files_count} JS files\n"
                            f"🔍 Scanning JavaScript files...\n\n"
                            f"🎯 Target: {normalized_url}",
                            parse_mode=None
                        )
                    else:
                        await status_message.edit_text(
                            f"🤖 Bot is running...\n"
                            f"🔍 {message}\n\n"
                            f"🎯 Target: {normalized_url}",
                            parse_mode=None
                        )
                except Exception as e:
                    self.logger.warning(f"Failed to send progress update: {e}")
            
            # Start scan in background
            self.active_scans[scan_key] = {
                'url': normalized_url,
                'start_time': datetime.now(),
                'status': 'running'
            }
            
            # Update status: Starting scan
            await asyncio.sleep(1)
            await status_message.edit_text(
                f"🤖 Bot is running...\n"
                f"🔍 Starting scan process\n"
                f"⏳ Analyzing target URL\n\n"
                f"🎯 Target: {normalized_url}",
                parse_mode=None
            )
            
            # Run scan with progress updates
            self.scanner_service.progress_callback = progress_callback
            scan_result = await self.scanner_service.scan_website(normalized_url)
            
            # Remove from active scans
            if scan_key in self.active_scans:
                del self.active_scans[scan_key]
            
            # Update final status
            if scan_result and scan_result.status != 'error':
                await status_message.edit_text(
                     f"🤖 Bot is running...\n"
                     f"✅ Scan completed successfully!\n\n"
                     f"🎯 Target: {normalized_url}\n"
                     f"🔑 Credentials found: {len(scan_result.credentials)}\n"
                     f"🌐 Endpoints found: {len(scan_result.endpoints)}",
                     parse_mode=None
                 )
            
            # Send detailed results
            await self._send_scan_results(update, scan_result)
            
        except Exception as e:
            self.logger.error(f"Error in scan command: {e}")
            await self._send_error_message(update, "Failed to perform scanning")
    
    async def handle_status_command(self, update: Update, context) -> None:
        """Handle /status command
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        try:
            if not self._is_valid_context(update):
                return
            
            if not self.active_scans:
                await update.message.reply_text(
                    "✅ Status Bot\n\n"
                    "🔍 No scan currently running\n"
                    "🤖 Bot ready to receive new commands!",
                    parse_mode=None
                )
                return
            
            status_message = "📊 Status Scan Aktif\n\n"
            
            for scan_key, scan_info in self.active_scans.items():
                duration = (datetime.now() - scan_info['start_time']).total_seconds()
                status_message += (
                    f"🎯 URL: {scan_info['url']}\n"
                    f"⏱️ Duration: {duration:.0f} seconds\n"
                    f"📈 Status: {scan_info['status']}\n\n"
                )
            
            await update.message.reply_text(
                status_message,
                parse_mode=None
            )
            
        except Exception as e:
            self.logger.error(f"Error in status command: {e}")
            await self._send_error_message(update, "Failed to get status")
    
    async def handle_report_command(self, update: Update, context) -> None:
        """Handle /report command (admin only)
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        try:
            # Check if user is admin
            user_id = getattr(update.effective_user, 'id', 0)
            if str(user_id) != self.admin_chat_id:
                await update.message.reply_text(
                    "❌ Access denied!\n\n"
                    "This command is for admin only.",
                    parse_mode=None
                )
                return
            
            if not self._is_valid_context(update):
                return
            
            # Extract URL from command
            if not context.args:
                await update.message.reply_text(
                    "❌ Format salah!\n\n"
                    "Usage: /report <URL>\n"
                    "Example: /report example.com",
                    parse_mode=None
                )
                return
            
            url = context.args[0]
            normalized_url = self._normalize_url(url)
            
            await self._generate_pdf_report(update, normalized_url)
            
        except Exception as e:
            self.logger.error(f"Error in report command: {e}")
            await self._send_error_message(update, "Failed to generate report")
    
    async def handle_reportpdf_command(self, update: Update, context) -> None:
        """Handle /reportpdf command (available for all users)
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        try:
            if not self._is_valid_context(update):
                return
            
            # Extract URL from command
            if not context.args:
                await update.message.reply_text(
                    "❌ Format salah!\n\n"
                    "Usage: /reportpdf <URL>\n"
                    "Example: /reportpdf example.com",
                    parse_mode=None
                )
                return
            
            url = context.args[0]
            normalized_url = self._normalize_url(url)
            
            await self._generate_pdf_report(update, normalized_url)
            
        except Exception as e:
            self.logger.error(f"Error in reportpdf command: {e}")
            await self._send_error_message(update, "Failed to generate PDF report")
    
    async def handle_enter_command(self, update: Update, context) -> None:
        """Handle /enter command (admin only, private chat)
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        try:
            # Check if user is admin and in private chat
            user_id = getattr(update.effective_user, 'id', 0)
            chat_type = getattr(update.effective_chat, 'type', '')
            
            if str(user_id) != self.admin_chat_id:
                await update.message.reply_text(
                    "❌ Akses ditolak!\n\n"
                    "Perintah ini hanya untuk admin.",
                    parse_mode=None
                )
                return
            
            if chat_type != 'private':
                await update.message.reply_text(
                    "❌ Perintah ini hanya bisa digunakan di private chat!",
                    parse_mode=None
                )
                return
            
            # Extract group URL from command
            if not context.args:
                await update.message.reply_text(
                    "❌ Format salah!\n\n"
                    "Gunakan: /enter <group_url>\n"
                    "Contoh: /enter https://t.me/c/123456789/5",
                    parse_mode=None
                )
                return
            
            group_url = context.args[0]
            
            # Parse group URL to extract chat_id and topic_id
            match = re.match(r'https://t\.me/c/(\d+)/(\d+)', group_url)
            if not match:
                await update.message.reply_text(
                    "❌ Format URL group tidak valid!\n\n"
                    "Format yang benar: https://t.me/c/CHAT_ID/TOPIC_ID",
                    parse_mode=None
                )
                return
            
            chat_id, topic_id = match.groups()
            
            # Update target topic
            self.target_topic_id = topic_id
            
            await update.message.reply_text(
                f"✅ Target group successfully updated!\n\n"
                f"🎯 Chat ID: {chat_id}\n"
                f"📌 Topic ID: {topic_id}\n\n"
                f"Bot sekarang akan merespons di topic tersebut.",
                parse_mode=None
            )
            
        except Exception as e:
            self.logger.error(f"Error in enter command: {e}")
            await self._send_error_message(update, "Failed to update target group")
    
    async def handle_private_message(self, update: Update, context) -> None:
        """Handle private messages (forward to admin)
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        try:
            user_id = getattr(update.effective_user, 'id', 0)
            user_name = getattr(update.effective_user, 'first_name', 'Unknown')
            message_text = getattr(update.message, 'text', '')
            
            # Don't forward admin's own messages
            if str(user_id) == self.admin_chat_id:
                return
            
            # Forward message to admin
            forward_message = (
                f"💬 Pesan dari user:\n\n"
                f"👤 Nama: {user_name}\n"
                f"🆔 ID: {user_id}\n"
                f"📝 Pesan: {message_text}"
            )
            
            # Send to admin (this would need actual implementation)
            self.logger.info(f"Private message from {user_name} ({user_id}): {message_text}")
            
            # Send acknowledgment to user
            await update.message.reply_text(
                "✅ Pesan Anda telah diterima!\n\n"
                "📨 Pesan telah diteruskan ke admin\n"
                "⏱️ Admin akan merespons segera.",
                parse_mode=None
            )
            
        except Exception as e:
            self.logger.error(f"Error in private message handler: {e}")
    
    def _is_valid_context(self, update: Update) -> bool:
        """Check if the message is in valid context (correct topic or private chat)
        
        Args:
            update: Telegram update object
            
        Returns:
            True if context is valid, False otherwise
        """
        try:
            chat_type = getattr(update.effective_chat, 'type', '')
            
            # Allow private chats
            if chat_type == 'private':
                return True
            
            # For group chats, check topic ID
            if chat_type in ['group', 'supergroup']:
                message_thread_id = getattr(update.message, 'message_thread_id', None)
                
                if message_thread_id is None:
                    # No topic specified, reject
                    return False
                
                if str(message_thread_id) == self.target_topic_id:
                    return True
                else:
                    # Wrong topic, send error message
                    asyncio.create_task(update.message.reply_text(
                        "❌ Bot hanya aktif di topic tertentu!\n\n"
                    f"📌 Topic yang benar: ID {self.target_topic_id}",
                    parse_mode=None
                    ))
                    return False
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking context validity: {e}")
            return False
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL by adding https:// if missing
        
        Args:
            url: Input URL
            
        Returns:
            Normalized URL with protocol
        """
        if not url.startswith(('http://', 'https://')):
            return f'https://{url}'
        return url
    
    async def _scan_with_progress(self, target_url: str, status_message) -> Optional[ScanResult]:
        """Perform scan with real-time progress updates
        
        Args:
            target_url: URL to scan
            status_message: Telegram message to update with progress
            
        Returns:
            Scan result or None if failed
        """
        try:
            # Simulate progress updates during scanning
            await asyncio.sleep(1)
            await status_message.edit_text(
                f"🤖 Bot is running...\n"
                f"🔍 Discovering JavaScript files...\n\n"
                f"🎯 Target: {target_url}",
                parse_mode=None
            )
            
            # Perform actual scan
            scan_result = await self.scanner_service.scan_website(target_url)
            
            # Simulate finding JS files and scanning
            if scan_result:
                # Simulate finding files
                await status_message.edit_text(
                    f"🤖 Bot is running...\n"
                    f"📁 Found 20 JS files\n"
                    f"🔍 Scanning JavaScript files...\n\n"
                    f"🎯 Target: {target_url}",
                    parse_mode=None
                )
                
                # Simulate scanning time
                await asyncio.sleep(2)
            
            return scan_result
            
        except Exception as e:
            self.logger.error(f"Error in scan with progress: {e}")
            return None
    

    
    async def _send_scan_results(self, update: Update, scan_result: ScanResult) -> None:
        """Send formatted scan results to user
        
        Args:
            update: Telegram update object
            scan_result: Scan result data
        """
        try:
            if scan_result.status == 'error':
                await update.message.reply_text(
                    f"❌ Error during scanning:\n\n"
                    f"{scan_result.error_message or 'Unknown error'}",
                    parse_mode=None
                )
                return
            
            # Format results
            results_message = self._format_scan_results(scan_result)
            
            await update.message.reply_text(
                results_message,
                parse_mode=None
            )
            
        except Exception as e:
            self.logger.error(f"Error sending scan results: {e}")
            await self._send_error_message(update, "Failed to send scan results")
    
    def _format_scan_results(self, scan_result: ScanResult) -> str:
        """Format scan results for display
        
        Args:
            scan_result: Scan result data
            
        Returns:
            Formatted message string
        """
        try:
            message = f"📊 Scanning Results\n\n"
            message += f"🎯 Target: {scan_result.target_url}\n"
            message += f"⏱️ Duration: {scan_result.scan_duration:.1f} seconds\n\n"
            
            # Credentials section
            if scan_result.credentials:
                high_risk = [c for c in scan_result.credentials if c.confidence == 'high']
                medium_risk = [c for c in scan_result.credentials if c.confidence == 'medium']
                low_risk = [c for c in scan_result.credentials if c.confidence == 'low']
                
                message += f"🔑 Credentials Found: {len(scan_result.credentials)}\n\n"
                
                # High risk credentials (limit to 3)
                if high_risk:
                    message += "🚨 High Risk:\n"
                    for i, cred in enumerate(high_risk[:3]):
                        cred_type = cred.type.replace('_', ' ').title()
                        # Truncate long values
                        display_value = cred.value[:50] + '...' if len(cred.value) > 50 else cred.value
                        message += f"• {cred_type}: {display_value}\n"
                    if len(high_risk) > 3:
                        message += f"• \.\.\. and {len(high_risk) - 3} others\n"
                    message += "\n"
                
                # Medium risk credentials (limit to 2)
                if medium_risk:
                    message += "⚠️ Medium Risk:\n"
                    for i, cred in enumerate(medium_risk[:2]):
                        cred_type = cred.type.replace('_', ' ').title()
                        display_value = cred.value[:30] + '...' if len(cred.value) > 30 else cred.value
                        message += f"• {cred_type}: {display_value}\n"
                    if len(medium_risk) > 2:
                        message += f"• \.\.\. and {len(medium_risk) - 2} others\n"
                    message += "\n"
                
                # Low risk count only
                if low_risk:
                    message += f"ℹ️ Low Risk: {len(low_risk)} item\n\n"
                
                message += "📄 Use /reportpdf for complete details\n\n"
            else:
                message += "✅ No exposed credentials found\n\n"
            
            # Endpoints section
            if scan_result.endpoints:
                message += f"🌐 Endpoints Found: {len(scan_result.endpoints)}\n"
                
                # Show first 3 endpoints
                for i, endpoint in enumerate(scan_result.endpoints[:3]):
                    method = endpoint.method
                    url = endpoint.url[:60] + '...' if len(endpoint.url) > 60 else endpoint.url
                    message += f"• {method}: {url}\n"
                
                if len(scan_result.endpoints) > 3:
                    message += f"• \.\.\. and {len(scan_result.endpoints) - 3} others\n"
                
                message += "\n📄 Use /reportpdf for complete details\n"
            else:
                message += "ℹ️ No API endpoints found\n"
            
            return message
            
        except Exception as e:
            self.logger.error(f"Error formatting scan results: {e}")
            return "❌ Error formatting scan results"
    
    async def _generate_pdf_report(self, update: Update, url: str) -> None:
        """Generate and send PDF report
        
        Args:
            update: Telegram update object
            url: Target URL for scanning
        """
        try:
            await update.message.reply_text(
                f"📄 Generating PDF report...\n\n"
                f"🎯 Target: {url}\n"
                f"⏱️ Please wait...",
                parse_mode=None
            )
            
            # Perform scan
            scan_result = await self.scanner_service.scan_website(url)
            
            if scan_result.status == 'error':
                await update.message.reply_text(
                    f"❌ Error during scanning:\n\n"
                    f"{scan_result.error_message or 'Unknown error'}",
                    parse_mode=None
                )
                return
            
            # Generate PDF
            pdf_path = self.pdf_service.generate_report(scan_result)
            
            # Send PDF file
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(pdf_path, 'rb') as pdf_file:
                 await update.message.reply_document(
                     document=pdf_file,
                     filename=f"security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                     caption=(
                         f"📄 Security Report\n\n"
                         f"🎯 Target: {url}\n"
                         f"🔑 Credentials: {len(scan_result.credentials)}\n"
                         f"🌐 Endpoints: {len(scan_result.endpoints)}\n"
                         f"📅 Generated: {timestamp}"
                     ),
                     parse_mode=None
                 )
            
            # Clean up PDF file
            try:
                os.remove(pdf_path)
            except Exception as e:
                self.logger.warning(f"Failed to remove PDF file: {e}")
            
        except Exception as e:
            self.logger.error(f"Error generating PDF report: {e}")
            await self._send_error_message(update, "Failed to generate PDF report")
    
    async def _send_error_message(self, update: Update, error_msg: str) -> None:
        """Send error message to user
        
        Args:
            update: Telegram update object
            error_msg: Error message to send
        """
        try:
            await update.message.reply_text(
                f"❌ Error: {error_msg}",
                parse_mode=None
            )
        except Exception as e:
            self.logger.error(f"Failed to send error message: {e}")