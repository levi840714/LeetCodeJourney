#!/usr/bin/env python3
"""
Script to verify all Dashboard sections are working correctly
"""
import os
import gspread
from dotenv import load_dotenv
import sys

sys.path.append('..')

# Load environment variables - try multiple paths
if os.path.exists('../.env'):
    load_dotenv('../.env')
elif os.path.exists('/Users/liumengfu/Desktop/leetcode_journey/.env'):
    load_dotenv('/Users/liumengfu/Desktop/leetcode_journey/.env')
else:
    # Fallback: set directly for this script
    os.environ['GOOGLE_SHEET_NAME'] = 'leetcode_journey'

def verify_dashboard_sections():
    """Verify all dashboard sections are present and working"""
    # Try multiple paths for credentials
    if os.path.exists('../credentials.json'):
        SERVICE_ACCOUNT_FILE = '../credentials.json'
    elif os.path.exists('/Users/liumengfu/Desktop/leetcode_journey/credentials.json'):
        SERVICE_ACCOUNT_FILE = '/Users/liumengfu/Desktop/leetcode_journey/credentials.json'
    else:
        print("❌ credentials.json not found in expected locations")
        return False
    SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME")
    
    if not SHEET_NAME:
        print("❌ GOOGLE_SHEET_NAME not found in .env file")
        return False
    
    try:
        gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
        spreadsheet = gc.open(SHEET_NAME)
        worksheet = spreadsheet.worksheet("Dashboard")
        
        print(f"🔍 Verifying Dashboard completeness in: {SHEET_NAME}")
        print("=" * 60)
        
        # Check key sections
        sections_to_check = [
            ("A1", "🎯 LeetCode Learning Analytics Dashboard", "Main Header"),
            ("A3", "📅 TODAY'S REVIEW REMINDERS", "Review Reminders"),
            ("D3", "📈 LEARNING PROGRESS", "Learning Progress"), 
            ("G3", "🎯 DIFFICULTY BREAKDOWN", "Difficulty Breakdown"),
            ("K3", "📊 LEARNING CURVE ANALYTICS", "Learning Curve Analytics"),
            ("K5", "📈 MONTHLY SOLVING TREND", "Monthly Trend"),
            ("K20", "🔥 TOPIC MASTERY HEATMAP", "Topic Mastery"),
            ("A15", "💡 SMART LEARNING RECOMMENDATIONS", "Smart Recommendations"),
            ("G9", "📊 REVIEW SUCCESS TREND", "Review Success Trend (Relocated)"),
            ("G27", "⚡ ADVANCED LEARNING METRICS", "Advanced Metrics (Relocated)"),
            ("N3", "🔥 LEARNING STREAK", "Learning Streak")
        ]
        
        print("📋 Checking Dashboard Sections:")
        print()
        
        all_good = True
        for cell, expected_start, description in sections_to_check:
            try:
                cell_value = worksheet.acell(cell).value
                if cell_value and expected_start in str(cell_value):
                    print(f"✅ {description} ({cell}): Found - '{cell_value}'")
                else:
                    print(f"❌ {description} ({cell}): Missing or incorrect - '{cell_value}'")
                    all_good = False
            except Exception as e:
                print(f"❌ {description} ({cell}): Error reading - {e}")
                all_good = False
        
        print()
        print("📊 Checking Data Sections:")
        print()
        
        # Check if data sections have content
        data_sections = [
            ("K7", "Monthly trend data"),
            ("K22", "Topic mastery data"), 
            ("G11", "Review success data (relocated)"),
            ("G28", "Advanced metrics data (relocated)")
        ]
        
        for cell, description in data_sections:
            try:
                cell_value = worksheet.acell(cell).value
                if cell_value and str(cell_value).strip() != "":
                    print(f"✅ {description} ({cell}): Has data")
                else:
                    print(f"⚠️  {description} ({cell}): No data (may be normal if no problems logged)")
            except Exception as e:
                print(f"❌ {description} ({cell}): Error reading - {e}")
                
        print()
        print("📈 Checking Charts/Sparklines:")
        print()
        
        # Check sparklines
        sparkline_sections = [
            ("N7", "Monthly trend sparkline"),
            ("H24", "Success rate sparkline (relocated)")
        ]
        
        for cell, description in sparkline_sections:
            try:
                cell_value = worksheet.acell(cell).value
                if cell_value and "SPARKLINE" in str(cell_value):
                    print(f"✅ {description} ({cell}): Chart formula present")
                else:
                    print(f"⚠️  {description} ({cell}): No chart formula")
            except Exception as e:
                print(f"❌ {description} ({cell}): Error reading - {e}")
        
        print()
        if all_good:
            print("🎉 Dashboard Verification PASSED!")
            print("✨ All main sections are present and properly configured")
        else:
            print("⚠️  Dashboard Verification completed with some issues")
            print("💡 Some sections may need manual adjustment")
            
        print()
        print("📊 Your Dashboard URL:")
        print(f"🔗 {spreadsheet.url}")
        
        return all_good
        
    except Exception as e:
        print(f"❌ Error verifying dashboard: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Dashboard Completeness Verification Tool")
    print()
    
    success = verify_dashboard_sections()
    if success:
        print("\n🚀 Your Dashboard is fully configured and ready to use!")
    else:
        print("\n💡 Your Dashboard has been set up but may need minor adjustments.")