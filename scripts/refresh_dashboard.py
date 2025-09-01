#!/usr/bin/env python3
"""
Script to refresh/recreate the Dashboard with new Learning Curve Analytics
Use this to update your existing Dashboard with the latest chart features
"""
import os
import gspread
from dotenv import load_dotenv

# Import the setup function from app.py (parent directory)
import sys
sys.path.append('..')
from app import setup_dashboard_sheet, setup_analysis_sheet
import time

# Load .env from parent directory
load_dotenv('../.env')

def setup_dashboard_with_delays(spreadsheet):
    """Setup complete dashboard with all advanced analytics and proper delays to avoid API rate limits"""
    print("🔧 Setting up complete Dashboard with Learning Curve Analytics...")
    print("⏳ This process includes all advanced features:")
    print("   📈 Monthly Problem Solving Trend Chart with sparklines")
    print("   🔥 Topic Mastery Heatmap with visual indicators")
    print("   📊 Review Success Rate Line Chart")
    print("   ⚡ Advanced Learning Metrics")
    print("   🎯 Complete visual formatting with borders and colors")
    print()
    
    # Use the complete setup function from app.py which includes all features
    # This function already handles the advanced analytics properly
    setup_dashboard_sheet(spreadsheet)
    
    print("✅ Complete dashboard with all Learning Curve Analytics features has been created!")
    print("🎉 Your dashboard now includes:")
    print("   • 📈 12-month trend visualization with column charts")
    print("   • 🔥 Topic mastery heatmap (🔥🔥🔥 = Master, 💧 = Beginner)")
    print("   • 📊 6-week review success rate tracking with line charts")
    print("   • ⚡ Advanced metrics: learning velocity, retention rate, difficulty progress")
    print("   • 🎯 Enhanced visual formatting with professional borders and colors")
    print("   • 🔗 Direct LeetCode hyperlinks for priority reviews")
    print("   • 📋 Smart recommendations and streak tracking")

def refresh_dashboard_with_charts():
    """Refresh the Dashboard with new Learning Curve Analytics charts"""
    # Use relative paths to parent directory since script is in scripts/
    SERVICE_ACCOUNT_FILE = '../credentials.json'
    SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME")
    
    if not SHEET_NAME:
        print("❌ GOOGLE_SHEET_NAME not found in .env file")
        return False
    
    try:
        gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
        spreadsheet = gc.open(SHEET_NAME)
        
        print(f"🔄 Refreshing Dashboard with new analytics in: {SHEET_NAME}")
        print("\n🎨 New features being added:")
        print("   📈 Monthly Problem Solving Trend Chart (12 months)")
        print("   🔥 Topic Mastery Heatmap with visual indicators")
        print("   📊 Review Success Rate Line Chart (8 weeks)")
        print("   ⚡ Advanced Learning Metrics")
        print("   ✨ Enhanced visual formatting and sparkline charts")
        
        # Force refresh Dashboard (will clear and recreate with new charts)
        print("\n🔧 Updating Dashboard with complete Learning Curve Analytics...")
        print("📊 This will recreate the dashboard with all advanced features")
        print()
        
        try:
            dashboard = spreadsheet.worksheet("Dashboard")
            print("📝 Found existing Dashboard sheet - will recreate with new content")
        except gspread.exceptions.WorksheetNotFound:
            print("📝 Dashboard sheet not found - will create new one")
        
        # Use complete dashboard setup
        setup_dashboard_with_delays(spreadsheet)
        print("✅ Dashboard updated with Learning Curve Analytics!")
        
        # Refresh Analysis sheet too
        print("\n📈 Updating Analysis sheet...")
        try:
            analysis = spreadsheet.worksheet("Analysis") 
            analysis.clear()  # Force clear to trigger recreation
        except gspread.exceptions.WorksheetNotFound:
            print("📝 Analysis sheet not found - will create new one")
            
        setup_analysis_sheet(spreadsheet)
        print("✅ Analysis sheet updated!")
        
        print("\n🎉 Dashboard refresh completed successfully!")
        print("\n📊 Your enhanced dashboard now includes:")
        print("   • 📈 Monthly trend visualization with sparkline column charts (12 months)")
        print("   • 🔥 Topic mastery heatmap (🔥🔥🔥 = Master, 💧 = Beginner)")
        print("   • 📊 Weekly review success rate line chart (6 weeks)")
        print("   • ⚡ Advanced metrics: learning velocity, retention rate, difficulty progress")
        print("   • 🎯 Professional visual formatting with borders and colors")
        print("   • 🔗 Direct clickable LeetCode hyperlinks for priority reviews")
        print("   • 📋 Smart recommendations and learning streak tracking")
        
        print(f"\n🔗 View your enhanced dashboard: https://docs.google.com/spreadsheets/d/{spreadsheet.id}")
        
        return True
        
    except gspread.exceptions.WorksheetNotFound as e:
        print(f"📝 Sheet not found: {e}")
        print("💡 The sheets will be created automatically when you submit your first problem")
        return False
        
    except Exception as e:
        print(f"❌ Error refreshing dashboard: {e}")
        print("💡 Try running the application and submitting a problem to recreate the dashboard")
        return False

if __name__ == "__main__":
    import sys
    
    # Check if running in auto mode (non-interactive)
    auto_mode = len(sys.argv) > 1 and sys.argv[1] == "--auto"
    
    print("🎯 LeetCode Dashboard Chart Upgrade Tool")
    print("=" * 50)
    print("This tool will upgrade your existing Dashboard with advanced analytics:")
    print("📈 Monthly Problem Solving Trends")
    print("🔥 Topic Mastery Heatmap") 
    print("📊 Review Success Rate Analysis")
    print("⚡ Advanced Learning Metrics")
    print()
    
    if auto_mode:
        print("🤖 Running in automatic mode...")
        proceed = True
    else:
        try:
            proceed = input("Continue with dashboard upgrade? (y/N): ").lower().startswith('y')
        except (EOFError, KeyboardInterrupt):
            proceed = False
            print("\nOperation cancelled")
    
    if proceed:
        success = refresh_dashboard_with_charts()
        if success:
            print("\n🚀 Upgrade complete! Open your Google Sheet to see the new analytics.")
        else:
            print("\n❌ Upgrade failed. Check your .env configuration and try again.")
    else:
        print("Operation cancelled")