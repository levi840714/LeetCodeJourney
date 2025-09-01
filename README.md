# LeetCode Journey 🚀

A comprehensive LeetCode learning progress tracker that automatically logs solved problems to Google Sheets using a Chrome extension frontend and Flask backend. Features intelligent spaced repetition for optimal review scheduling and advanced analytics dashboard.

## 🎯 Features

### Chrome Extension
- **Auto-detect problem details** from LeetCode pages
- **Smart topic tagging** with 24 predefined categories
- **Configurable API endpoints** (local development + Cloud Functions)
- **One-click logging** with notes support
- **Auto-detection** of best available API endpoint

### Backend API
- **Flask-based REST API** with Google Sheets integration
- **Spaced repetition algorithm** for review scheduling
- **Duplicate problem detection** with review tracking
- **Automatic sheet formatting** and data validation
- **Cloud Functions deployment** support

### Google Sheets Integration
- **Problems sheet**: Optimized 10-column layout with hyperlinks
- **Analysis sheet**: Automated topic statistics and performance metrics
- **Dashboard sheet**: Comprehensive learning analytics with charts
- **Auto-formatting**: Professional styling with conditional formatting
- **Review system**: Tracks review history and calculates next review dates

### Advanced Analytics
- **Monthly solving trends** with sparkline charts
- **Topic mastery heatmap** with difficulty analysis
- **Review success rate tracking** over time
- **Learning velocity metrics** and streak tracking
- **Smart recommendations** for priority reviews

## 🛠 Quick Start

### Prerequisites
- **Python 3.11+** with pip
- **Google Cloud Project** (for Sheets API)
- **Chrome Browser** (for extension)
- **Service Account JSON** from Google Cloud Console

### 1. Environment Setup

```bash
# Clone and enter directory
git clone <repository-url>
cd leetcode_journey

# Install dependencies
make install
```

### 2. Google Sheets API Setup

1. **Create Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project or select existing one

2. **Enable APIs**:
   ```bash
   gcloud services enable sheets.googleapis.com
   gcloud services enable drive.googleapis.com
   ```

3. **Create Service Account**:
   - Go to IAM & Admin → Service Accounts
   - Create service account with Sheets API access
   - Download JSON key as `credentials.json`

4. **Create Google Sheet**:
   - Create new Google Sheet
   - Share with service account email (Editor access)
   - Copy sheet name for configuration

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Required settings**:
```env
GOOGLE_SHEET_NAME="Your-LeetCode-Sheet-Name"
```

### 4. Local Development

```bash
# Start Flask development server
make run

# Server runs on http://127.0.0.1:5000
```

### 5. Chrome Extension Installation

1. **Load Extension**:
   - Open Chrome → Extensions → Developer mode
   - Click "Load unpacked"
   - Select `chrome_extension/` folder

2. **Configure Extension**:
   - Visit any LeetCode problem page
   - Click extension icon → "⚙️ Settings"
   - Select "Local Development" (auto-detected)
   - Click "Save"

## ☁️ Cloud Functions Deployment

Deploy to Google Cloud Functions for serverless operation:

### Quick Deployment
```bash
# Simple deployment (recommended)
./cloud-deploy-simple.sh

# Full deployment with options
./deploy-cf.sh
```

### Manual Deployment
```bash
# Set project and enable APIs
gcloud config set project YOUR_PROJECT_ID
gcloud services enable cloudfunctions.googleapis.com

# Deploy function
cp requirements-cf.txt requirements.txt
gcloud functions deploy leetcode-journey \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point leetcode_journey \
  --source . \
  --region us-central1

# Get function URL
gcloud functions describe leetcode-journey \
  --region=us-central1 \
  --format="value(httpsTrigger.url)"
```

### Configure Extension for Cloud Functions
1. Open extension settings
2. Select "☁️ Cloud Functions"
3. Paste your function URL
4. Click "Save" and "Test"

## 📊 Usage

### Logging Problems
1. **Navigate** to any LeetCode problem page
2. **Solve** the problem (submit successful solution)
3. **Click** the LeetCode Journey extension icon
4. **Review** auto-filled problem details
5. **Select** relevant topics and add notes
6. **Click** "Save to Google Sheet"

### Review System
- **Easy problems**: Review after 14 days
- **Medium problems**: Review after 7 days  
- **Hard problems**: Review after 3 days
- **Exponential backoff**: Intervals increase with each review (2.5x multiplier)
- **Maximum interval**: Capped at 365 days

### Analytics Dashboard
Access your Google Sheet to view:
- **Today's review reminders** with due counts
- **Monthly solving trends** with visual charts
- **Topic mastery analysis** with heat indicators
- **Learning velocity** and success rate metrics
- **Smart recommendations** for priority reviews

## 🔧 Development Commands

```bash
# Environment
make install              # Install Python dependencies
make clean               # Remove cache files

# Development
make run                 # Start Flask server

# Google Sheets Tools
make format-sheets      # Apply formatting to existing sheets
make upgrade-dashboard  # Add advanced analytics (with rate limiting)
make test-scripts       # Test utility scripts

# Cloud Functions
./deploy-cf.sh          # Interactive deployment
./cloud-deploy-simple.sh # Quick deployment
```

## 📁 Project Structure

```
leetcode_journey/
├── app.py                    # Main Flask backend server
├── main.py                   # Cloud Functions entry point
├── chrome_extension/         # Chrome extension files
│   ├── manifest.json        # Extension configuration  
│   ├── popup.html/js/css    # Main extension UI
│   ├── config-simple.js     # Configuration management
│   ├── quick-settings.html  # Settings page
│   └── content_script.js    # DOM scraping logic
├── scripts/                  # Utility scripts
│   ├── format_existing_sheets.py  # Sheet formatting
│   └── refresh_dashboard.py       # Dashboard upgrade
├── deploy-cf.sh             # Cloud Functions deployment
├── requirements.txt         # Python dependencies
├── requirements-cf.txt      # Cloud Functions dependencies
├── credentials.json         # Google Service Account key
├── .env                     # Environment configuration
└── Makefile                # Build automation
```

## 🎨 Data Structure

### Problems Sheet (10 columns)
| Column | Content | Description |
|---------|---------|-------------|
| A | Problem Number | Hyperlinked LeetCode problem number |
| B | Problem Name | Full problem title |
| C | Difficulty | Easy/Medium/Hard with color coding |
| D | Topics | Comma-separated topic tags |
| E | Date | Initial submission date |
| F | Next Review | Calculated next review date |
| G | Review Count | Number of review sessions |
| H | Last Review | Most recent review date |
| I | Review History | Semicolon-separated review dates |
| J | Notes | Detailed learning notes (max width) |

### Spaced Repetition Algorithm
```python
# Base intervals by difficulty
base_interval = {"Easy": 14, "Medium": 7, "Hard": 3}

# Exponential backoff formula
next_interval = base_interval * (2.5 ^ review_count)
max_interval = min(next_interval, 365)  # Cap at 1 year
```

## 🔐 Security & Privacy

- **Local storage**: All data stored in your Google Sheets
- **Service account**: Uses Google Cloud service account authentication
- **CORS protection**: Configured for Chrome extension origins only
- **No data collection**: Extension does not transmit data to third parties
- **Open source**: Full code visibility and audit capability

## 🚀 Advanced Features

### Topic Categories (24 types)
Array, Hash Table, Linked List, Math, Two Pointers, String, Binary Search, Sliding Window, Dynamic Programming, Backtracking, Stack, Heap, Greedy, Graph, Trie, Tree, Binary Tree, Depth-First Search, Breadth-First Search, Union Find, Bit Manipulation, Recursion, Sorting, Design

### Dashboard Analytics
- **Learning Curve**: 12-month trend analysis with sparklines
- **Topic Mastery**: Heat map with mastery scoring system  
- **Review Success**: 8-week rolling success rate analysis
- **Advanced Metrics**: Velocity, retention rate, difficulty progress
- **Smart Recommendations**: Priority review list with direct links

### Configuration Options
- **Dual mode support**: Local development + Cloud Functions
- **Auto-detection**: Automatically finds best available endpoint
- **Connection testing**: Built-in connectivity verification
- **Storage management**: Chrome extension local storage for settings
- **Error handling**: Graceful fallbacks and user feedback

## 🛟 Troubleshooting

### Common Issues

**Extension not working**:
- Refresh LeetCode page
- Check if extension is loaded in Chrome
- Verify API endpoint in settings

**API connection failed**:
- Local: Ensure Flask server is running (`make run`)
- Cloud: Verify Cloud Function URL in extension settings
- Test connection using settings page

**Google Sheets errors**:
- Verify service account has Editor access to sheet
- Check `credentials.json` file exists and is valid
- Ensure Google Sheets API is enabled

**Cloud Functions deployment**:
- Verify Google Cloud CLI is installed and authenticated
- Check project billing is enabled
- Ensure required APIs are enabled

### Debug Commands
```bash
# View Cloud Functions logs
gcloud functions logs read leetcode-journey --region=us-central1

# Test local API
curl -X GET http://127.0.0.1:5000/

# Verify Google Sheets access
python -c "import gspread; print('Sheets API OK')"
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google Sheets API** for seamless data integration
- **Chrome Extensions** for browser automation capabilities
- **Flask** for lightweight web framework
- **LeetCode** for providing the platform that inspired this tool

---

**Happy coding and keep grinding! 🎯**

*Built with ❤️ for the programming community*