#!/bin/bash
# VPS Deployment Script for Trading Bot
# Run this on your VPS to set up the trading system

echo "🚀 Setting up Trading Bot on VPS..."

# Update system
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git screen

# Create directory
mkdir -p ~/trading-bot
cd ~/trading-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install alpaca-py yfinance pandas numpy ta python-dotenv colorama termcolor

# Create startup script
cat > start_trading.sh << 'EOF'
#!/bin/bash
cd ~/trading-bot
source venv/bin/activate
python3 main.py >> trading.log 2>&1
EOF

chmod +x start_trading.sh

# Create systemd service for auto-restart
sudo tee /etc/systemd/system/trading-bot.service << EOF
[Unit]
Description=Trading Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/trading-bot
ExecStart=/home/$USER/trading-bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable trading-bot
sudo systemctl start trading-bot

echo "✅ Trading Bot deployed!"
echo "📊 Check status: sudo systemctl status trading-bot"
echo "📋 View logs: sudo journalctl -u trading-bot -f"
echo "🛑 Stop bot: sudo systemctl stop trading-bot"
echo "▶️  Start bot: sudo systemctl start trading-bot"
