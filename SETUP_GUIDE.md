# 🎯 Telegram Bot Setup Guide

## ✅ Configuration Overview

### 🤖 Bot Information
- **Bot Token**: Configure in `.env` file
- **Target Group**: Set your Telegram group URL
- **Chat ID**: Your group's chat ID
- **Topic ID**: Specific topic ID for bot responses

## 📋 Setup Steps

### 1. 🔧 Bot Preparation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd "Credential & Endpoint Seeker Pentest Tool"
   ```

2. **Setup virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### 2. 👥 Telegram Group Setup

1. **Add Bot to Group**:
   - Open your target Telegram group
   - Click "Add Members" or "+"
   - Search for your bot by username
   - Add bot to the group

2. **Grant Bot Permissions**:
   - Ensure bot has permissions for:
     - ✅ Send Messages
     - ✅ Read Messages
     - ✅ Delete Messages (optional)

3. **Configure Topic-Specific Operation**:
   - Bot only responds in the specified **Topic ID**
   - Messages in other topics are ignored
   - To change topic, edit `TARGET_TOPIC_ID` in `.env` file

### 3. 🧪 Testing the Bot

In the correct topic, try these commands:

```
/start
```
```
/help
```
```
/scan https://example.com
```
```
/status
```

### 4. 👑 Admin Features - Change Target Group

**For Admin users only**, you can dynamically change the target group:

**In Private Chat with Bot:**
```
/enter https://t.me/c/CHAT_ID/TOPIC_ID
```

**Example:**
```
/enter https://t.me/c/1234567890/5
```

The bot will:
- ✅ Parse Telegram group URL
- ✅ Update target topic in real-time
- ✅ Confirm the change
- ✅ Start responding in the new topic

### 5. 💬 Private Message Feature

- Users can send private messages to the bot
- Bot forwards these messages to the admin
- Admin can reply through the bot

## ⚠️ Important Notes

### 🔒 Security
- Bot only operates in designated topics
- Credentials stored securely in `.env` file
- `.env` file is included in `.gitignore`

### 🎯 Usage Guidelines
- **Group Chat**: Only in specified Topic ID
- **Private Chat**: All messages forwarded to admin
- **Scanning**: Only scan websites you own or have permission to test

### 🔧 Troubleshooting

**Bot not responding in group?**
- Ensure bot is added to the group
- Check if messages are sent in the correct topic
- Verify bot has sufficient permissions

**Bot not running?**
```bash
# Check status
python3 main.py

# Or with Docker
docker-compose up -d
docker-compose logs -f telegram-recon-bot
```

**Need to change configuration?**
- Edit `.env` file
- Restart bot: `Ctrl+C` then `python3 main.py`

## 🚀 Production Deployment

### Using Docker
```bash
# Build and run
docker-compose up -d

# Check logs
docker-compose logs -f telegram-recon-bot

# Stop bot
docker-compose down
```

### Using PM2 (Process Manager)
```bash
# Install PM2
npm install -g pm2

# Run bot
pm2 start main.py --name "telegram-recon-bot" --interpreter python3

# Monitor
pm2 monit

# Logs
pm2 logs telegram-recon-bot
```

### Environment Variables

Make sure your `.env` file contains:
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

---

**✅ Bot is ready to use!** 

For further assistance, use the `/help` command in the bot or read the complete documentation in `README.md`.