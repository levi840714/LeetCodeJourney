#!/usr/bin/env python3
"""
Format existing sheets with proper column widths and alignment
Run this if you want to format sheets that were created before the formatting feature
"""
import os
import gspread
from dotenv import load_dotenv
import sys

# Import formatting functions from main app (parent directory)
sys.path.append('..')
from app import apply_problems_formatting, apply_analysis_formatting, apply_dashboard_formatting

# Load .env from parent directory
load_dotenv('../.env')

def format_existing_sheets():
    """Format all existing sheets with proper layout"""
    # Use relative paths to parent directory since script is in scripts/
    SERVICE_ACCOUNT_FILE = '../credentials.json'
    SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME")
    
    if not SHEET_NAME:
        print("❌ GOOGLE_SHEET_NAME not found in .env file")
        return False
    
    try:
        gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
        spreadsheet = gc.open(SHEET_NAME)
        
        print(f"🎨 Formatting existing sheets in: {SHEET_NAME}")
        
        # Format each sheet type
        sheet_configs = [
            ("Problems", apply_problems_formatting, "📊 Main data sheet"),
            ("Analysis", apply_analysis_formatting, "📈 Topic statistics"),
            ("Dashboard", apply_dashboard_formatting, "🎯 Learning analytics")
        ]
        
        success_count = 0
        
        for sheet_name, format_function, description in sheet_configs:
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
                print(f"🔧 Formatting {sheet_name} - {description}")
                format_function(worksheet)
                print(f"✅ {sheet_name} formatted successfully!")
                success_count += 1
                
            except gspread.exceptions.WorksheetNotFound:
                print(f"⚠️  {sheet_name} sheet not found - skipping")
            except Exception as e:
                print(f"❌ Error formatting {sheet_name}: {e}")
        
        if success_count > 0:
            print(f"\n🎉 Successfully formatted {success_count} sheets!")
            print("\n📊 Your Google Sheets now have:")
            print("   ✅ Optimal column widths")
            print("   ✅ Professional alignment (center/left as appropriate)")
            print("   ✅ Text wrapping for Notes and Review History")
            print("   ✅ Top alignment for multi-line text")
            print("   ✅ Clean, readable layout")
            
            print(f"\n🔗 View your formatted sheets: https://docs.google.com/spreadsheets/d/{spreadsheet.id}")
        else:
            print("❌ No sheets were formatted")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Error accessing spreadsheet: {e}")
        return False

if __name__ == "__main__":
    print("🎨 Google Sheets Formatting Tool")
    print("=" * 40)
    
    print("This tool will format your existing sheets with:")
    print("• Proper column widths for readability")
    print("• Smart alignment (numbers center, text left)")
    print("• Professional appearance")
    print()
    
    if input("Continue? (y/N): ").lower().startswith('y'):
        format_existing_sheets()
    else:
        print("Operation cancelled")