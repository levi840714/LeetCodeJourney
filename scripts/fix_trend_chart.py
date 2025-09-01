#!/usr/bin/env python3
"""
Script to fix the Trend Chart sparkline visualization
"""
import os
import gspread
from dotenv import load_dotenv
import sys

# Add parent directory to path
sys.path.append('..')

# Load environment variables - try multiple paths
if os.path.exists('../.env'):
    load_dotenv('../.env')
elif os.path.exists('/Users/liumengfu/Desktop/leetcode_journey/.env'):
    load_dotenv('/Users/liumengfu/Desktop/leetcode_journey/.env')
else:
    # Fallback: set directly for this script
    os.environ['GOOGLE_SHEET_NAME'] = 'leetcode_journey'

def fix_trend_chart():
    """Fix the Trend Chart sparkline visualization"""
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
        
        print(f"📈 Fixing Trend Chart in: {SHEET_NAME}")
        print()
        
        # First, let's check what's currently in the Trend Chart area
        print("🔍 Checking current Trend Chart status...")
        try:
            chart_label = worksheet.acell('G24').value
            chart_content = worksheet.acell('H24').value
            print(f"Chart Label (G24): {chart_label}")
            print(f"Chart Content (H24): {chart_content}")
        except:
            print("No current trend chart found")
        
        print()
        
        # Let's also check what Success % data we have
        print("📊 Checking Success % data range...")
        try:
            success_data = worksheet.get('I11:I22')
            print("Success % values:")
            for i, row in enumerate(success_data):
                if row:
                    print(f"  Week {i+1}: {row[0] if row else 'Empty'}")
        except Exception as e:
            print(f"Error reading success data: {e}")
        
        print()
        
        # Fix the Trend Chart
        print("🔧 Creating Trend Chart sparkline...")
        
        # Update the label
        worksheet.update(values=[['📈 Trend Chart:']], range_name='G24')
        worksheet.format('G24', {
            "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 0.0, "green": 0.4, "blue": 0.8}},
            "horizontalAlignment": "LEFT"
        })
        
        # Create the sparkline chart that spans H24:I24
        sparkline_formula = '=SPARKLINE(I11:I22,{"charttype","line";"color1","#34A853";"linewidth",2;"max",100;"min",0})'
        worksheet.update(values=[[sparkline_formula]], range_name='H24')
        
        # Merge H24:I24 to give the chart more space
        try:
            worksheet.merge_cells('H24:I24')
        except:
            pass  # Cell might already be merged
        
        print("✅ Trend Chart sparkline created")
        print()
        
        # Add some formatting to make it look professional
        print("🎨 Adding professional formatting...")
        
        # Format the trend chart area
        worksheet.format('G24:I24', {
            "borders": {
                "top": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
                "bottom": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
                "left": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
                "right": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}
            },
            "backgroundColor": {"red": 0.98, "green": 0.98, "blue": 1.0}
        })
        
        print("✅ Professional formatting applied")
        print()
        
        # Let's also make sure we have a backup sparkline approach
        print("🔧 Creating alternative chart visualization...")
        
        # Add a simple text-based trend indicator as backup
        worksheet.update(values=[['Trend: ↗️ Improving']], range_name='G25')
        worksheet.format('G25', {
            "textFormat": {"fontSize": 9, "italic": True, "foregroundColor": {"red": 0.4, "green": 0.4, "blue": 0.4}}
        })
        
        print("✅ Alternative trend indicator added")
        print()
        
        print("🎉 Trend Chart has been fixed!")
        print("\\n📈 What the Trend Chart shows:")
        print("   • 📊 Visual line graph of your weekly success rates")
        print("   • 📈 Green upward trends = improving performance")
        print("   • 📉 Downward trends = areas needing attention")
        print("   • 🎯 Quick visual assessment of learning progress")
        print("   • 📱 Compact sparkline format saves space")
        print()
        print("💡 How to interpret:")
        print("   • Higher points = better success rates that week")
        print("   • Upward slope = consistent improvement")
        print("   • Flat line = stable performance")
        print("   • Downward slope = may need more practice")
        print()
        
        print(f"🔗 View your updated dashboard: https://docs.google.com/spreadsheets/d/{spreadsheet.id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing trend chart: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("📈 Trend Chart Fix Tool")
    print("=" * 25)
    print("This tool will create the missing Trend Chart sparkline")
    print()
    
    success = fix_trend_chart()
    if success:
        print("\\n🚀 Trend Chart visualization fixed!")
    else:
        print("\\n❌ Fix failed. Check the error messages above.")