# 🤖 Solana ML Scanner

Smart Solana memecoin opportunity scanner with ML - Telegram alerts, real-time analysis, auto-learning

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-success)

## 🌟 Features

### Core Features
- **🔍 Multi-Source Scanning**: Monitors Pump.fun, Raydium, and DexScreener for new tokens
- **🤖 Machine Learning**: Auto-learns from market data to predict pump probability
- **📊 Rule-Based Scoring**: Combines ML predictions with traditional technical analysis
- **⚡ Real-Time Alerts**: Instant Telegram/Discord notifications for high-score opportunities
- **🛡️ Safety Checks**: Built-in rug detection, honeypot checks, and holder analysis
- **📈 Dashboard**: Streamlit-powered web dashboard for monitoring and configuration

### ML Capabilities
- **Pump Probability Predictor**: Estimates likelihood of price increase
- **Magnitude Estimator**: Predicts potential gain percentage
- **Rug Detector**: Identifies suspicious patterns and red flags
- **Pattern Matcher**: Recognizes successful token launch patterns

### Alert Categories
1. **Fast Sniper** (Score 80-100): Ultra-early catches with high ML confidence
2. **Smart Sniper** (Score 70-79): Early opportunities with good fundamentals
3. **Momentum** (Score 60-69): Established tokens with building momentum
4. **Safe** (Score 50-59): Lower risk, slower growth opportunities

## 📋 Requirements

- Python 3.9 or higher
- Telegram Bot Token (for alerts)
- Helius RPC API Key (for Solana data)
- 100€+ capital recommended for testing

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/Azeflow10/solana-ml-scanner.git
cd solana-ml-scanner

# Install dependencies
pip install -r requirements.txt

# Setup database and directories
python scripts/setup_database.py
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env

# Copy config template
cp config.yaml.example config.yaml

# Customize config (optional)
nano config.yaml
```

### 3. Get API Keys

#### Required: Telegram Bot
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Create new bot with `/newbot`
3. Copy the bot token to `.env`
4. Get your chat ID from [@userinfobot](https://t.me/userinfobot)

#### Required: Helius RPC
1. Sign up at [helius.dev](https://helius.dev)
2. Create a new project
3. Copy API key to `.env`

#### Optional: Additional APIs
- **DexScreener**: Better rate limits (optional)
- **Birdeye**: Additional market data (optional)
- **RugCheck**: Enhanced rug detection (optional)

### 4. Test Telegram Integration

```bash
# Test your Telegram bot setup
python scripts/test_telegram.py

# This will:
# - Verify bot token and chat ID
# - Send test messages
# - Test alert formatting with buttons
# - Confirm everything is working
```

### 5. Run the Bot

```bash
# Start the scanner
python main.py

# In another terminal, start the dashboard (optional)
streamlit run dashboard/streamlit_app.py
```

## 📖 Usage

### Basic Operation

Once running, the bot will:
1. **Scan** multiple sources for new token launches
2. **Analyze** each token (liquidity, holders, contract safety)
3. **Score** using rule-based + ML predictions
4. **Alert** you via Telegram for high-score opportunities
5. **Learn** from market outcomes to improve predictions

### Telegram Commands

- `/start` - Start receiving alerts
- `/stop` - Pause alerts
- `/stats` - View your trading statistics
- `/config` - Adjust settings
- `/help` - Show all commands

### Dashboard Features

Access at `http://localhost:8501` after running:
- **Live Alerts**: Real-time opportunity feed
- **Your Trades**: Track performance and P&L
- **ML Insights**: Model accuracy and predictions
- **Analytics**: Market trends and patterns
- **Configuration**: Adjust settings visually

## ⚙️ Configuration

### Key Settings in `config.yaml`

```yaml
alerts:
  min_score: 75              # Minimum score to trigger alert
  min_ml_confidence: 0.70    # ML confidence threshold
  
  filters:
    min_liquidity_usd: 15000  # Minimum liquidity required
    min_holders: 20           # Minimum holder count
    min_rugcheck_score: 8.0   # Rug safety threshold (0-10)
    max_top10_concentration: 40  # Max % held by top 10 holders

machine_learning:
  ml_weight: 0.40            # ML influence (40%)
  rule_weight: 0.60          # Rule-based influence (60%)

trading:
  default_position_sol: 0.06  # Default position size
  take_profit_percent: 150    # Target profit
  stop_loss_percent: -20      # Stop loss
```

## 🤖 Machine Learning

### Training Strategy

The bot uses a **hybrid approach**:

1. **Cold Start**: Begins with rule-based scoring only
2. **Data Collection**: Learns from 100-200 real market events
3. **Model Training**: Trains personalized models from your data
4. **Continuous Learning**: Retrains every 24 hours with new data

### Why This Approach?

- **Personalized**: Learns YOUR trading style and risk preferences
- **Adaptive**: Adjusts to current market conditions
- **Safe**: Starts conservatively, improves over time
- **No Overfitting**: Real market data prevents bias

### Optional: Pre-trained Models

```bash
# Download community-trained models (coming soon)
python scripts/download_pretrained_models.py
```

## 📁 Project Structure

```
solana-ml-scanner/
├── main.py                 # Entry point
├── requirements.txt        # Dependencies
├── config.yaml            # Configuration
├── .env                   # API keys (not committed)
│
├── src/
│   ├── core/              # Core orchestration
│   ├── scanners/          # Token discovery
│   ├── analyzers/         # Safety & metrics
│   ├── scoring/           # Rule-based scoring
│   ├── ml/                # Machine learning
│   ├── notifications/     # Alerts (Telegram/Discord)
│   ├── database/          # Data persistence
│   └── utils/             # Helpers
│
├── dashboard/             # Streamlit web UI
├── scripts/              # Setup & maintenance
├── tests/                # Test suite
├── data/                 # Database & logs
└── models/               # Trained ML models
```

## 🔒 Security

### Built-in Safety Features

- ✅ **Rug Detection**: ML-powered suspicious pattern recognition
- ✅ **Honeypot Check**: Simulates sells before alerting
- ✅ **Holder Analysis**: Flags concentrated ownership
- ✅ **Liquidity Verification**: Ensures sufficient liquidity
- ✅ **Dev Reputation**: Tracks developer history
- ✅ **Blacklist Support**: Block known scammers

### Best Practices

1. **Start Small**: Test with minimum position sizes
2. **Diversify**: Never go all-in on one token
3. **Use Stop Losses**: Protect your capital
4. **Monitor Actively**: Check alerts promptly
5. **Review Performance**: Learn from wins and losses

## 📊 Performance Tracking

The bot automatically tracks:
- Win rate and average gains
- ML model accuracy
- Alert success rate
- Risk-adjusted returns
- Best performing patterns

Access via Dashboard → "Your Trades" tab.

## 🛠️ Development

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_scanners.py

# With coverage
python -m pytest --cov=src tests/
```

### Adding Custom Scanners

1. Create new scanner in `src/scanners/`
2. Inherit from base scanner class
3. Implement `scan()` method
4. Register in `orchestrator.py`

### Custom ML Models

1. Add model in `src/ml/models/`
2. Implement training in `src/ml/training/`
3. Update `MLPredictor` to use new model

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## ⚠️ Disclaimer

This software is for educational purposes only. Cryptocurrency trading carries significant risk. Always do your own research and never invest more than you can afford to lose. The developers are not responsible for any financial losses.

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Azeflow10/solana-ml-scanner/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Azeflow10/solana-ml-scanner/discussions)
- **Updates**: Watch this repo for updates

## 🗺️ Roadmap

- [x] Initial release with core features
- [ ] Pre-trained model distribution
- [ ] Advanced pattern recognition
- [ ] Multi-wallet support
- [ ] Automated trading (with Jupiter)
- [ ] Mobile app
- [ ] Community model sharing

## 🙏 Acknowledgments

Built with:
- [Solana Web3](https://github.com/michaelhly/solana-py)
- [Streamlit](https://streamlit.io)
- [scikit-learn](https://scikit-learn.org)
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)

---

**Made with ❤️ for the Solana community**

Star ⭐ this repo if you find it useful!
