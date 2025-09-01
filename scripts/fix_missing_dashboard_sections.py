#!/usr/bin/env python3
"""
Script to fix missing sections in the Dashboard
This script will manually add the missing advanced analytics sections
"""
import os
import gspread
from dotenv import load_dotenv
import sys

# Add parent directory to path to import from app.py
sys.path.append('..')
load_dotenv('../.env')

def fix_missing_dashboard_sections():
    """Add missing dashboard sections that weren't created properly"""
    SERVICE_ACCOUNT_FILE = '../credentials.json'
    SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME")
    
    if not SHEET_NAME:
        print("❌ GOOGLE_SHEET_NAME not found in .env file")
        return False
    
    try:
        gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
        spreadsheet = gc.open(SHEET_NAME)
        worksheet = spreadsheet.worksheet("Dashboard")
        
        print(f"🔧 Fixing missing sections in Dashboard: {SHEET_NAME}")
        print()
        
        # === 1. FIX TOPIC MASTERY HEATMAP (K22 and below) ===
        print("🔥 Adding Topic Mastery Heatmap content...")
        
        common_topics = ['Array', 'Hash Table', 'Two Pointers', 'String', 'Dynamic Programming', 
                        'Binary Search', 'Tree', 'Graph', 'Stack', 'Linked List']
        
        heatmap_formulas = []
        for i, topic in enumerate(common_topics):
            row_idx = 22 + i
            mastery_formula = f'=IF(COUNTIF(Problems!D:D,"*{topic}*")>0, (COUNTIF(Problems!D:D,"*{topic}*")*10) - (AVERAGEIFS(Problems!G:G,Problems!D:D,"*{topic}*")*2), 0)'
            heat_formula = f'=IF(L{row_idx}>0, ROUND(N{row_idx}/10,0), 0)'
            
            heatmap_formulas.append([
                topic,
                f'=COUNTIF(Problems!D:D,"*{topic}*")',
                f'=IF(COUNTIF(Problems!D:D,"*{topic}*")>0, ROUND(AVERAGEIFS(Problems!G:G,Problems!D:D,"*{topic}*"),1), "-")',
                mastery_formula,
                heat_formula
            ])
        
        worksheet.update(f'K22:O{21+len(common_topics)}', heatmap_formulas, value_input_option='USER_ENTERED')
        
        # Add visual indicators for mastery levels
        for i, topic in enumerate(common_topics):
            row_idx = 22 + i
            heat_indicator_formula = f'=IF(N{row_idx}>=50,"🔥🔥🔥",IF(N{row_idx}>=30,"🔥🔥",IF(N{row_idx}>=10,"🔥",IF(N{row_idx}>0,"💧",""))))'
            worksheet.update(f'O{row_idx}', [[heat_indicator_formula]], value_input_option='USER_ENTERED')
        
        # Add legend
        worksheet.update('P21', [['Heat Legend:']])
        worksheet.format('P21', {"textFormat": {"bold": True, "fontSize": 10}})
        
        legend_data = [
            ['🔥🔥🔥 Master (50+)'],
            ['🔥🔥 Good (30+)'], 
            ['🔥 Learning (10+)'],
            ['💧 Beginner (1+)']
        ]
        worksheet.update('P22:P25', legend_data)
        worksheet.format('P22:P25', {"textFormat": {"fontSize": 9}})
        
        print("✅ Topic Mastery Heatmap content added")
        print()
        
        # === 2. ADD REVIEW SUCCESS TREND (A35 to avoid conflict) ===
        print("📊 Adding Review Success Trend chart...")
        
        worksheet.update('A35', [['📊 REVIEW SUCCESS TREND']])
        worksheet.format('A35', {"textFormat": {"bold": True, "fontSize": 12, "foregroundColor": {"red": 0.0, "green": 0.7, "blue": 0.0}}})
        
        success_headers = ['Week', 'Reviews', 'Success %', 'Trend', 'Chart']
        worksheet.update('A36:E36', [success_headers])
        worksheet.format('A36:E36', {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}})
        
        # Calculate weekly review success rates
        success_formulas = []
        for i in range(6):
            week_start = f'TODAY()-{(5-i)*7}'
            week_end = f'TODAY()-{(5-i)*7-6}' 
            week_label = f'=TEXT({week_start},"MM/DD")'
            
            total_reviews = f'=COUNTIFS(Problems!H:H,">="&{week_start},Problems!H:H,"<="&{week_end})'
            success_rate = f'=IF({total_reviews}>0, ROUND((COUNTIFS(Problems!H:H,">="&{week_start},Problems!H:H,"<="&{week_end},Problems!G:G,"<=3")/{total_reviews})*100,1), 0)'
            
            success_formulas.append([
                week_label,
                total_reviews,
                success_rate,
                f'=IF(C{37+i}>0, IF(C{37+i}>=80,"🟢",IF(C{37+i}>=60,"🟡","🔴")), "")',
                ''
            ])
        
        worksheet.update('A37:E42', success_formulas, value_input_option='USER_ENTERED')
        
        # Add sparkline for success rate trend
        worksheet.update('E37', [['=SPARKLINE(C37:C42,{"charttype","line";"color1","#34A853";"linewidth",2})']], value_input_option='USER_ENTERED')
        
        print("✅ Review Success Trend chart added")
        print()
        
        # === 3. ADD ADVANCED LEARNING METRICS (G35) ===
        print("⚡ Adding Advanced Learning Metrics...")
        
        worksheet.update('G35', [['⚡ ADVANCED LEARNING METRICS']])
        worksheet.format('G35', {"textFormat": {"bold": True, "fontSize": 12, "foregroundColor": {"red": 0.4, "green": 0.2, "blue": 0.8}}})
        
        advanced_metrics = [
            ['📚 Learning Velocity:', '=ROUND(COUNTA(Problems!A:A)/(DATEDIF(MIN(Problems!E:E),TODAY(),"D")+1),2)&" problems/day"'],
            ['🎯 Retention Rate:', '=ROUND((COUNTIFS(Problems!G:G,1)/COUNTA(Problems!A:A))*100,1)&"%"'],
            ['🔥 Difficulty Progress:', '=ROUND((COUNTIF(Problems!C:C,"Hard")/(COUNTA(Problems!A:A)-1))*100,1)&"% Hard"'],
            ['🏆 Topic Diversity:', '=COUNTA(Analysis!A:A)-3&" different topics"']
        ]
        
        worksheet.update('G36:H39', advanced_metrics, value_input_option='USER_ENTERED')
        worksheet.format('G36:G39', {"textFormat": {"bold": True}})
        worksheet.format('H36:H39', {"textFormat": {"bold": True, "fontSize": 12, "foregroundColor": {"red": 0.0, "green": 0.6, "blue": 0.0}}})
        
        print("✅ Advanced Learning Metrics added")
        print()
        
        # === 4. ADD LEARNING STREAK (N3) ===
        print("🔥 Adding Learning Streak...")
        
        worksheet.update('N3', [['🔥 LEARNING STREAK']])
        worksheet.format('N3', {"textFormat": {"bold": True, "fontSize": 12, "foregroundColor": {"red": 1.0, "green": 0.4, "blue": 0.0}}})
        
        worksheet.update('N4', [['Current Streak:']])
        worksheet.update('O4', [['=COUNTA(Problems!E:E)-1&" Problems"']], value_input_option='USER_ENTERED')
        worksheet.format('O4', {"textFormat": {"bold": True, "fontSize": 14, "foregroundColor": {"red": 1.0, "green": 0.4, "blue": 0.0}}})
        
        print("✅ Learning Streak added")
        print()
        
        print("🎉 All missing dashboard sections have been added!")
        print("\n📊 Your dashboard now includes:")
        print("   • 🔥 Complete Topic Mastery Heatmap with 10 topics")
        print("   • 📊 Review Success Trend chart (6 weeks)")
        print("   • ⚡ Advanced Learning Metrics (velocity, retention, etc.)")
        print("   • 🔥 Learning Streak tracking")
        print()
        
        print(f"🔗 View your complete dashboard: https://docs.google.com/spreadsheets/d/{spreadsheet.id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing dashboard sections: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Dashboard Section Fix Tool")
    print("=" * 40)
    print("This tool will add missing sections to your Dashboard:")
    print("🔥 Topic Mastery Heatmap content")
    print("📊 Review Success Trend chart")
    print("⚡ Advanced Learning Metrics") 
    print("🔥 Learning Streak tracking")
    print()
    
    success = fix_missing_dashboard_sections()
    if success:
        print("\n🚀 Fix completed! Your dashboard should now have all sections.")
    else:
        print("\n❌ Fix failed. Check your .env configuration and try again.")