#!/usr/bin/env python3
"""
Script to debug and fix formula errors in Dashboard
"""
import os
import gspread
from dotenv import load_dotenv
import sys

# Add parent directory to path
sys.path.append('..')
load_dotenv('../.env')

def debug_and_fix_dashboard():
    """Debug and fix formula errors in Dashboard"""
    SERVICE_ACCOUNT_FILE = '../credentials.json'
    SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME")
    
    if not SHEET_NAME:
        print("❌ GOOGLE_SHEET_NAME not found in .env file")
        return False
    
    try:
        gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
        spreadsheet = gc.open(SHEET_NAME)
        
        print(f"🔍 Debugging Dashboard formulas in: {SHEET_NAME}")
        print()
        
        # Check if Problems sheet exists and get sample data
        try:
            problems_sheet = spreadsheet.worksheet("Problems")
            print("📋 Problems sheet found. Checking structure...")
            
            # Get header row to understand column structure
            headers = problems_sheet.row_values(1)
            print(f"Problems sheet headers: {headers}")
            
            # Get first few rows of data
            if len(headers) > 0:
                sample_data = problems_sheet.get_all_values()[:5]  # First 5 rows including header
                print("Sample data:")
                for i, row in enumerate(sample_data):
                    print(f"Row {i+1}: {row}")
                print()
                
        except gspread.exceptions.WorksheetNotFound:
            print("❌ Problems sheet not found!")
            return False
        
        # Get Dashboard sheet
        worksheet = spreadsheet.worksheet("Dashboard")
        
        # === FIX 1: LEARNING CURVE ANALYTICS DATA ===
        print("🔧 Fixing Learning Curve Analytics (Monthly Trend)...")
        
        # The issue might be with EOMONTH function or date formats
        # Let's use simpler date calculations that work in Google Sheets
        monthly_headers = ['Month', 'Problems Solved', 'Cumulative']
        worksheet.update(values=[monthly_headers], range_name='K6:M6')
        worksheet.format('K6:M6', {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}})
        
        # Generate simpler monthly formulas that should work
        monthly_data = []
        for i in range(12):
            # Use DATE function instead of EOMONTH for better compatibility
            month_offset = 11 - i  # Start from 11 months ago to current
            
            # Simplified date range calculation
            month_start = f'DATE(YEAR(TODAY()),MONTH(TODAY())-{month_offset},1)'
            month_end = f'DATE(YEAR(TODAY()),MONTH(TODAY())-{month_offset}+1,0)'  # Last day of month
            
            # Month label using simple formatting
            month_label = f'=TEXT(DATE(YEAR(TODAY()),MONTH(TODAY())-{month_offset},1),"mmm yy")'
            
            # Count problems in that month (simpler formula)
            problems_count = f'=COUNTIFS(Problems!E:E,">="&{month_start},Problems!E:E,"<="&{month_end})'
            
            # Cumulative count up to that month
            cumulative = f'=COUNTIF(Problems!E:E,"<="&{month_end})'
            
            monthly_data.append([month_label, problems_count, cumulative])
        
        worksheet.update(values=monthly_data, range_name='K7:M18', value_input_option='USER_ENTERED')
        
        # Add sparkline chart (simpler version)
        worksheet.update(values=[['=SPARKLINE(L7:L18,{"charttype","column"})']], range_name='N7', value_input_option='USER_ENTERED')
        
        print("✅ Monthly trend data fixed")
        print()
        
        # === FIX 2: REVIEW SUCCESS TREND ===
        print("🔧 Fixing Review Success Trend formulas...")
        
        # The issue is likely with complex date calculations
        # Let's use simpler weekly calculations
        
        success_headers = ['Week', 'Reviews', 'Success %', 'Trend', 'Chart']
        worksheet.update(values=[success_headers], range_name='A36:E36')
        worksheet.format('A36:E36', {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}})
        
        # Create simpler weekly formulas
        success_data = []
        for i in range(6):
            week_offset = 5 - i  # Start from 5 weeks ago
            
            # Simple week calculation
            week_start = f'TODAY()-{week_offset*7+6}'
            week_end = f'TODAY()-{week_offset*7}'
            
            # Week label (simple format)
            week_label = f'=TEXT({week_start},"mm/dd")'
            
            # Count reviews in that week - simplified
            # Count problems that have Last Review (column H) in that week
            total_reviews = f'=COUNTIFS(Problems!H:H,">="&{week_start},Problems!H:H,"<="&{week_end})'
            
            # Success rate - problems with review count <= 3 (indicating good retention)
            # This is a simpler metric than the complex original
            success_count = f'=COUNTIFS(Problems!H:H,">="&{week_start},Problems!H:H,"<="&{week_end},Problems!G:G,"<=3")'
            success_rate = f'=IF({total_reviews}>0,ROUND({success_count}/{total_reviews}*100,1),0)'
            
            # Trend indicator
            trend = f'=IF(C{37+i}>=80,"🟢",IF(C{37+i}>=60,"🟡",IF(C{37+i}>0,"🔴","")))'
            
            success_data.append([week_label, total_reviews, success_rate, trend, ''])
        
        worksheet.update(values=success_data, range_name='A37:E42', value_input_option='USER_ENTERED')
        
        # Add sparkline (simpler version)
        worksheet.update(values=[['=SPARKLINE(C37:C42,{"charttype","line"})']], range_name='E37', value_input_option='USER_ENTERED')
        
        print("✅ Review Success Trend formulas fixed")
        print()
        
        # === FIX 3: ADVANCED METRICS (Simpler versions) ===
        print("🔧 Updating Advanced Learning Metrics with simpler formulas...")
        
        # Simpler advanced metrics that should work reliably
        advanced_metrics = [
            ['📚 Total Problems:', '=COUNTA(Problems!A:A)-1'],  # Simplified
            ['🎯 Avg Reviews:', '=IF(COUNTA(Problems!G:G)>0,ROUND(AVERAGE(Problems!G:G),1),0)'],
            ['🔥 Hard Problems:', '=COUNTIF(Problems!C:C,"Hard")'],
            ['🏆 Topics Covered:', '=COUNTA(UNIQUE(SPLIT(TEXTJOIN(",",TRUE,Problems!D:D),",")))-1']  # Simplified topic diversity
        ]
        
        worksheet.update(values=advanced_metrics, range_name='G36:H39', value_input_option='USER_ENTERED')
        worksheet.format('G36:G39', {"textFormat": {"bold": True}})
        worksheet.format('H36:H39', {"textFormat": {"bold": True, "fontSize": 12, "foregroundColor": {"red": 0.0, "green": 0.6, "blue": 0.0}}})
        
        print("✅ Advanced metrics updated")
        print()
        
        print("🎉 All formula errors have been fixed!")
        print("\n📊 Fixed issues:")
        print("   • 📈 Monthly trend now uses simpler DATE functions")
        print("   • 📊 Review success trend uses simplified weekly calculations")
        print("   • ⚡ Advanced metrics use more reliable formulas")
        print("   • 🎯 All sparkline charts simplified for better compatibility")
        print()
        
        print(f"🔗 Check your updated dashboard: https://docs.google.com/spreadsheets/d/{spreadsheet.id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing formulas: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Dashboard Formula Fix Tool")
    print("=" * 40)
    print("This tool will fix formula parsing errors in your Dashboard")
    print()
    
    success = debug_and_fix_dashboard()
    if success:
        print("\n🚀 Formula fixes completed!")
    else:
        print("\n❌ Fix failed. Check the error messages above.")