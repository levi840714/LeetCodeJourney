#!/usr/bin/env python3
"""
Script to relocate and fix REVIEW SUCCESS TREND and ADVANCED LEARNING METRICS
Move these sections to G-I columns (rows 9-33) and fix formula errors
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

def relocate_and_fix_sections():
    """Relocate REVIEW SUCCESS TREND and ADVANCED LEARNING METRICS to G-I area and fix errors"""
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
        
        print(f"🔧 Relocating and fixing dashboard sections in: {SHEET_NAME}")
        print()
        
        # === 1. CLEAR OLD SECTIONS AND MOVE TO G-I AREA ===
        print("🧹 Clearing old sections and preparing G-I area...")
        
        # Clear the target G-I area (rows 9-33) first
        worksheet.batch_clear(['G9:I33'])
        
        # Clear old problematic sections if they exist
        try:
            worksheet.batch_clear(['A35:F45', 'G35:H45'])  # Clear old locations
        except:
            pass  # Ignore if ranges don't exist
        
        print("✅ Old sections cleared")
        print()
        
        # === 2. ADD REVIEW SUCCESS TREND TO G9-I25 ===
        print("📊 Adding REVIEW SUCCESS TREND to G9-I25...")
        
        # Header
        worksheet.update('G9', [['📊 REVIEW SUCCESS TREND']])
        worksheet.format('G9', {
            "textFormat": {"bold": True, "fontSize": 12, "foregroundColor": {"red": 0.0, "green": 0.7, "blue": 0.0}},
            "horizontalAlignment": "CENTER"
        })
        
        # Merge header across G9:I9
        worksheet.merge_cells('G9:I9')
        
        # Column headers
        headers = ['Week', 'Reviews', 'Success %']
        worksheet.update('G10:I10', [headers])
        worksheet.format('G10:I10', {
            "textFormat": {"bold": True}, 
            "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
            "horizontalAlignment": "CENTER"
        })
        
        # Create 12 weeks of data (simplified formulas to avoid errors)
        success_data = []
        for i in range(12):
            week_offset = 11 - i  # Start from 11 weeks ago to current
            row_num = 11 + i
            
            # Simple week label
            week_label = f'=TEXT(TODAY()-{week_offset*7},"MM/DD")'
            
            # Count reviews (problems with Last Review in that week)
            week_start = f'TODAY()-{week_offset*7+6}'
            week_end = f'TODAY()-{week_offset*7}'
            total_reviews = f'=COUNTIFS(Problems!H:H,">="&{week_start},Problems!H:H,"<="&{week_end})'
            
            # Success rate - simplified calculation
            # Success = problems that needed 3 or fewer reviews total
            success_rate = f'=IF({total_reviews}>0,ROUND(COUNTIFS(Problems!H:H,">="&{week_start},Problems!H:H,"<="&{week_end},Problems!G:G,"<=3")/{total_reviews}*100,1),"")'
            
            success_data.append([week_label, total_reviews, success_rate])
        
        worksheet.update('G11:I22', success_data, value_input_option='USER_ENTERED')
        
        # Add sparkline chart to show trend
        worksheet.update('G24', [['📈 Trend Chart:']])
        worksheet.format('G24', {"textFormat": {"bold": True, "fontSize": 10}})
        worksheet.update('H24:I24', [['=SPARKLINE(I11:I22,{"charttype","line";"color1","#34A853";"linewidth",2})']])
        
        print("✅ Review Success Trend relocated and fixed")
        print()
        
        # === 3. ADD ADVANCED LEARNING METRICS TO G27-I33 ===
        print("⚡ Adding Advanced Learning Metrics to G27-I33...")
        
        # Header
        worksheet.update('G27', [['⚡ ADVANCED LEARNING METRICS']])
        worksheet.format('G27', {
            "textFormat": {"bold": True, "fontSize": 12, "foregroundColor": {"red": 0.4, "green": 0.2, "blue": 0.8}},
            "horizontalAlignment": "CENTER"
        })
        
        # Merge header across G27:I27
        worksheet.merge_cells('G27:I27')
        
        # Advanced metrics with simplified formulas
        metrics_data = [
            ['📚 Total Problems:', '=COUNTA(Problems!A:A)-1', 'problems'],
            ['🎯 Avg Reviews:', '=IF(COUNTA(Problems!G:G)>1,ROUND(AVERAGE(Problems!G2:G),1),0)', 'per problem'],
            ['🔥 Hard Problems:', '=COUNTIF(Problems!C:C,"Hard")', 'solved'],
            ['🏆 Active Streak:', '=COUNTA(Problems!A:A)-1', 'problems'],
            ['📈 This Month:', '=COUNTIFS(Problems!E:E,">="&EOMONTH(TODAY(),-1)+1)', 'problems'],
            ['💪 Success Rate:', '=IF(COUNTA(Problems!G:G)>1,ROUND(COUNTIFS(Problems!G:G,"<=2")/(COUNTA(Problems!G:G)-1)*100,1),100)', '%']
        ]
        
        worksheet.update('G28:I33', metrics_data, value_input_option='USER_ENTERED')
        
        # Format metrics
        worksheet.format('G28:G33', {"textFormat": {"bold": True}})
        worksheet.format('H28:H33', {
            "textFormat": {"bold": True, "fontSize": 12, "foregroundColor": {"red": 0.0, "green": 0.6, "blue": 0.0}},
            "horizontalAlignment": "RIGHT"
        })
        worksheet.format('I28:I33', {
            "textFormat": {"fontSize": 10, "italic": True},
            "horizontalAlignment": "LEFT"
        })
        
        print("✅ Advanced Learning Metrics relocated and fixed")
        print()
        
        # === 4. ADD BORDERS AND FINAL FORMATTING ===
        print("🎨 Adding borders and final formatting...")
        
        # Add borders around sections
        worksheet.format('G9:I25', {
            "borders": {
                "top": {"style": "SOLID", "color": {"red": 0.7, "green": 0.7, "blue": 0.7}},
                "bottom": {"style": "SOLID", "color": {"red": 0.7, "green": 0.7, "blue": 0.7}},
                "left": {"style": "SOLID", "color": {"red": 0.7, "green": 0.7, "blue": 0.7}},
                "right": {"style": "SOLID", "color": {"red": 0.7, "green": 0.7, "blue": 0.7}}
            }
        })
        
        worksheet.format('G27:I33', {
            "borders": {
                "top": {"style": "SOLID", "color": {"red": 0.7, "green": 0.7, "blue": 0.7}},
                "bottom": {"style": "SOLID", "color": {"red": 0.7, "green": 0.7, "blue": 0.7}},
                "left": {"style": "SOLID", "color": {"red": 0.7, "green": 0.7, "blue": 0.7}},
                "right": {"style": "SOLID", "color": {"red": 0.7, "green": 0.7, "blue": 0.7}}
            }
        })
        
        print("✅ Formatting completed")
        print()
        
        print("🎉 Section relocation completed successfully!")
        print("\\n📊 Updated layout:")
        print("   • 📊 Review Success Trend: G9-I25 (12 weeks of data)")
        print("   • ⚡ Advanced Learning Metrics: G27-I33 (6 key metrics)")
        print("   • 🔧 All formula errors fixed with simplified calculations")
        print("   • 📈 Sparkline trend chart included")
        print("   • 🎨 Professional borders and formatting applied")
        print()
        
        print(f"🔗 View your updated dashboard: https://docs.google.com/spreadsheets/d/{spreadsheet.id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error relocating sections: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Dashboard Section Relocation Tool")
    print("=" * 45)
    print("This tool will:")
    print("📊 Move REVIEW SUCCESS TREND to G9-I25")
    print("⚡ Move ADVANCED LEARNING METRICS to G27-I33") 
    print("🔧 Fix all #ERROR! formula issues")
    print("🎨 Apply professional formatting")
    print()
    
    success = relocate_and_fix_sections()
    if success:
        print("\\n🚀 Relocation completed! Check your dashboard.")
    else:
        print("\\n❌ Relocation failed. Check the error messages above.")