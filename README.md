# Telegram Recon Bot

A professional security reconnaissance bot for detecting credentials and API endpoints in websites. Built with Python using MVP (Model-View-Presenter) architecture pattern.

## 🎯 Features

### Security Scanning
- **Credential Detection**: API keys, access tokens, secret keys
- **Endpoint Discovery**: API endpoints from JavaScript files
- **Multi-format Support**: Firebase, AWS, Google API keys
- **PDF Reports**: Professional security assessment reports

### Bot Operations
- **Group Chat Support**: Operates within specific topics only
- **Private Messaging**: Direct communication with admin
- **Concurrent Scanning**: Multiple scans with rate limiting
- **Real-time Status**: Live scanning progress and statistics

## 🏗️ Architecture

This project follows MVP (Model-View-Presenter) pattern with clear separation of concerns:

```
├── main.py                 # Entry point and configuration
├── models/                 # Data models
│   └── scan_result.py     # Scan result data structures
├── services/              # Business logic
│   ├── scanner_service.py # Website scanning logic
│   └── pdf_service.py     # PDF report generation
├── presenters/            # User interaction logic
│   └── bot_presenter.py   # Telegram bot handlers
└── reports/               # Generated PDF reports
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Telegram Bot Token
- Virtual environment (recommended)

### Installation

1. **Clone and setup**:
   ```bash
   git clone <repository>
   cd "Credential & Endpoint Seeker Pentest Tool"
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the bot**:
   ```bash
   python3 main.py
   ```

## ⚙️ Configuration

Create a `.env` file with the following variables:

```env
# Required
BOT_TOKEN=your_telegram_bot_token
ADMIN_CHAT_ID=your_telegram_user_id
TARGET_TOPIC_ID=group_topic_id

# Optional
MAX_FILE_SIZE=5242880
REQUEST_TIMEOUT=30
MAX_CONCURRENT_SCANS=3
```

## 🤖 Bot Commands

### Group Chat Commands (Topic-specific)
- `/start` - Welcome message and bot introduction
- `/help` - Display available commands and usage
- `/scan <URL>` - Scan website for credentials and endpoints
- `/status` - Show bot status and active scans
- `/report <URL>` - Generate PDF security report

### Private Chat Commands
- `/enter <group_url>` - Set target group (Admin only)
- Any message - Forward to admin

### Usage Examples
```
/scan example.com          # Auto-adds https://
/scan https://example.com  # Full URL
/report https://target.com # Generate PDF report
```

## 📊 Detection Capabilities

### Credential Types
- **API Keys**: Firebase, AWS, Google Cloud
- **Access Tokens**: Bearer tokens, OAuth tokens
- **Secret Keys**: Application secrets
- **Database Credentials**: Connection strings

### Endpoint Detection
- **Absolute URLs**: `https://api.example.com/v1/users`
- **Relative Paths**: `/api/v1/data`
- **JavaScript Endpoints**: Extracted from JS files

## 🐳 Docker Support

### Using Docker Compose
```bash
docker-compose up -d
```

### Manual Docker Build
```bash
docker build -t telegram-recon-bot .
docker run -d --env-file .env telegram-recon-bot
```

## 📋 Dependencies

- `python-telegram-bot==20.7` - Telegram Bot API
- `aiohttp==3.9.1` - Async HTTP client
- `beautifulsoup4==4.12.2` - HTML parsing
- `reportlab==4.0.7` - PDF generation
- `python-dotenv==1.0.0` - Environment management

## 🔒 Security Considerations

### Bot Security
- **Topic Isolation**: Only responds in designated group topics
- **Admin Verification**: Restricted admin commands
- **Rate Limiting**: Prevents abuse with concurrent scan limits
- **Input Validation**: URL and parameter sanitization

### Scanning Ethics
- **Permission Required**: Only scan websites you own or have permission to test
- **Responsible Disclosure**: Report findings to website owners
- **Legal Compliance**: Follow local laws and regulations

## 📈 Monitoring

### Logging
The bot provides comprehensive logging:
- Application startup and configuration
- Scan progress and results
- Error handling and debugging
- User interactions and commands

### Status Monitoring
- Active scan count tracking
- Bot uptime statistics
- Error rate monitoring

## 🛠️ Development

### Project Structure
```
├── models/
│   └── scan_result.py     # Data classes for scan results
├── services/
│   ├── scanner_service.py # Core scanning functionality
│   └── pdf_service.py     # Report generation service
├── presenters/
│   └── bot_presenter.py   # Telegram bot interaction layer
├── main.py                # Application entry point
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── docker-compose.yml    # Multi-container setup
└── .env.example          # Environment template
```

### Adding New Features
1. **Models**: Add data structures in `models/`
2. **Services**: Implement business logic in `services/`
3. **Presenters**: Handle user interactions in `presenters/`
4. **Integration**: Wire components in `main.py`

## 📝 License

This project is for educational and authorized security testing purposes only.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes following MVP pattern
4. Add tests and documentation
5. Submit a pull request

## ⚠️ Disclaimer

This tool is intended for authorized security testing only. Users are responsible for ensuring they have proper permission before scanning any websites. The developers are not responsible for any misuse of this tool.