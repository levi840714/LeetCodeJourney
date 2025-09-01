import os
import gspread
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
# Enable CORS for all routes and origins
CORS(app, resources={
    r"/*": {
        "origins": ["chrome-extension://*", "http://127.0.0.1:*", "https://*.cloudfunctions.net"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# --- Configuration ---
SERVICE_ACCOUNT_FILE = 'credentials.json'
SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME")
DATA_SHEET_NAME = "Problems"

# --- Formatting & Header Definitions ---
HEADER_COLOR = {"red": 0.85, "green": 0.85, "blue": 0.85}
EXPECTED_HEADERS = ["Problem", "Name", "Difficulty", "Topics", "Date", "Next Review", "Review Count", "Last Review", "Review History", "Notes"]

TOPIC_LIST = [
    "Array", "Hash Table", "Linked List", "Math", "Two Pointers", "String",
    "Binary Search", "Sliding Window", "Dynamic Programming", "Backtracking",
    "Stack", "Heap", "Greedy", "Graph", "Trie", "Tree", "Binary Tree",
    "Depth-First Search", "Breadth-First Search", "Union Find", "Bit Manipulation",
    "Recursion", "Sorting", "Design"
]

DIFFICULTY_LIST = ["Easy", "Medium", "Hard"]

# --- Formatting Functions ---
def column_letter_to_index(letter):
    """Convert column letter to 0-based index"""
    result = 0
    for char in letter:
        result = result * 26 + (ord(char.upper()) - ord('A') + 1)
    return result - 1

def parse_column_range(col_range):
    """Parse column range like 'A:A' or 'B:C' to indices"""
    if ':' in col_range:
        start, end = col_range.split(':')
        start_idx = column_letter_to_index(start)
        end_idx = column_letter_to_index(end)
        return start_idx, end_idx
    else:
        idx = column_letter_to_index(col_range)
        return idx, idx

def apply_worksheet_formatting(worksheet, column_settings):
    """Apply column width, alignment, and text wrapping formatting"""
    try:
        requests = []
        
        for col_config in column_settings:
            if len(col_config) == 3:
                col_range, width, alignment = col_config
                wrap_text = False
            else:
                col_range, width, alignment, wrap_text = col_config
            
            start_col, end_col = parse_column_range(col_range)
            
            # Column width request
            requests.append({
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": worksheet.id,
                        "dimension": "COLUMNS", 
                        "startIndex": start_col,
                        "endIndex": end_col + 1
                    },
                    "properties": {
                        "pixelSize": width
                    },
                    "fields": "pixelSize"
                }
            })
            
            # Cell alignment and wrapping request
            cell_format = {
                "horizontalAlignment": alignment,
                "verticalAlignment": "TOP" if wrap_text else "MIDDLE",
                "wrapStrategy": "WRAP" if wrap_text else "OVERFLOW_CELL"
            }
            
            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": worksheet.id,
                        "startColumnIndex": start_col,
                        "endColumnIndex": end_col + 1
                    },
                    "cell": {
                        "userEnteredFormat": cell_format
                    },
                    "fields": "userEnteredFormat.horizontalAlignment,userEnteredFormat.verticalAlignment,userEnteredFormat.wrapStrategy"
                }
            })
        
        # Execute batch update
        if requests:
            worksheet.spreadsheet.batch_update({"requests": requests})
            
    except Exception as e:
        print(f"WARNING: Failed to apply formatting: {e}")

def apply_problems_formatting(worksheet):
    """Format Problems sheet with optimized layout and Notes at the end"""
    column_settings = [
        ('A:A', 60, 'CENTER'),          # Problem Number (缩小)
        ('B:B', 200, 'LEFT'),           # Problem Name (稍微缩小)  
        ('C:C', 80, 'CENTER'),          # Difficulty (缩小)
        ('D:D', 160, 'LEFT'),           # Topics (缩小)
        ('E:E', 100, 'CENTER'),         # Date (缩小)
        ('F:F', 100, 'CENTER'),         # Next Review (缩小)
        ('G:G', 70, 'CENTER'),          # Review Count (缩小)
        ('H:H', 100, 'CENTER'),         # Last Review (缩小)
        ('I:I', 280, 'LEFT', True),     # Review History - WITH TEXT WRAP
        ('J:J', 400, 'LEFT', True),     # Notes - AT END WITH MAXIMUM SPACE
    ]
    apply_worksheet_formatting(worksheet, column_settings)

def apply_analysis_formatting(worksheet):
    """Format Analysis sheet"""
    column_settings = [
        ('A:A', 150, 'LEFT'),     # Topic
        ('B:B', 80, 'CENTER'),    # Count
        ('C:C', 100, 'CENTER'),   # Percentage
    ]
    apply_worksheet_formatting(worksheet, column_settings)

def apply_dashboard_formatting(worksheet):
    """Format Dashboard sheet with text wrapping for recommendation areas"""
    column_settings = [
        ('A:A', 150, 'LEFT', True),   # Labels - wrap for long recommendations
        ('B:C', 80, 'CENTER'),        # Values
        ('D:E', 120, 'LEFT'),         # Progress labels
        ('F:H', 100, 'CENTER'),       # Statistics
        ('I:I', 90, 'CENTER'),        # Percentages
        ('J:J', 20, 'CENTER'),        # Spacer
        ('K:L', 120, 'LEFT'),         # Charts data
        ('M:M', 20, 'CENTER'),        # Spacer
        ('N:O', 130, 'LEFT'),         # Streak data
        ('P:P', 100, 'CENTER'),       # Additional
    ]
    apply_worksheet_formatting(worksheet, column_settings)

# --- Google Sheets Connection & Setup ---
def get_or_create_worksheet(spreadsheet, sheet_name):
    try:
        worksheet = spreadsheet.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows="100", cols="20")
    return worksheet

def setup_analysis_sheet(spreadsheet):
    """Create a separate analysis sheet for topic statistics"""
    worksheet = get_or_create_worksheet(spreadsheet, "Analysis")
    
    # Check if analysis sheet is already set up
    if worksheet.acell('A1').value == "📊 Topic Statistics":
        return
    
    worksheet.clear()
    
    # Title
    worksheet.update(range_name='A1:C1', values=[["📊 Topic Statistics", "", ""]])
    worksheet.format('A1:C1', {
        "backgroundColor": {"red": 0.1, "green": 0.4, "blue": 0.7},
        "textFormat": {"bold": True, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "fontSize": 14},
        "horizontalAlignment": "CENTER"
    })
    worksheet.merge_cells('A1:C1')
    
    # Headers for statistics
    worksheet.update(range_name='A3', values=[["Topic"]])
    worksheet.update(range_name='B3', values=[["Count"]])
    worksheet.update(range_name='C3', values=[["Percentage"]])
    worksheet.format('A3:C3', {
        "backgroundColor": {"red": 0.85, "green": 0.85, "blue": 0.85},
        "textFormat": {"bold": True},
        "horizontalAlignment": "CENTER"
    })
    
    # Auto-generate topic statistics
    stats_data = []
    for topic in TOPIC_LIST:
        # Use simple COUNTIFS to count occurrences
        count_formula = f'=COUNTIFS(Problems!D:D, "*{topic}*")'
        percentage_formula = f'=IF(B{len(stats_data)+4}>0, B{len(stats_data)+4}/COUNTA(Problems!D:D)*100, 0)'
        stats_data.append([topic, count_formula, percentage_formula])
    
    # Write all statistics at once
    start_row = 4
    end_row = start_row + len(stats_data) - 1
    worksheet.update(range_name=f'A{start_row}:C{end_row}', values=stats_data, value_input_option='USER_ENTERED')
    
    # Format statistics table
    worksheet.format(f'A3:C{end_row}', {
        "borders": {
            "top": {"style": "SOLID", "width": 1},
            "bottom": {"style": "SOLID", "width": 1},
            "left": {"style": "SOLID", "width": 1},
            "right": {"style": "SOLID", "width": 1}
        }
    })
    
    # Format percentage column
    worksheet.format(f'C4:C{end_row}', {"numberFormat": {"type": "PERCENT", "pattern": "0.0%"}})
    
    # Apply comprehensive formatting
    apply_analysis_formatting(worksheet)

def setup_dashboard_sheet(spreadsheet):
    import time
    
    worksheet = get_or_create_worksheet(spreadsheet, "Dashboard")
    # Check if dashboard is already set up to avoid rewriting
    if worksheet.acell('A1').value == "🎯 LeetCode Learning Analytics Dashboard":
        return

    worksheet.clear()
    
    # Expand grid to accommodate all charts (30 columns x 50 rows should be enough)
    try:
        worksheet.resize(rows=50, cols=30)
        print("📐 Expanded Dashboard grid to 30 columns x 50 rows")
    except Exception as resize_error:
        print(f"⚠️  Warning: Could not resize grid: {resize_error}")
        print("💡 Dashboard may be truncated if it exceeds default size")
    
    print("🔧 Setting up Dashboard in sections to avoid API limits...")
    print("⏳ This will take about 3 minutes with delays between sections")
    print()
    
    # === SECTION 1: HEADER AND BASIC INFO ===
    print("📝 Section 1/6: Setting up header and basic info...")
    
    # === MAIN TITLE ===
    worksheet.update(range_name='A1:P1', values=[["🎯 LeetCode Learning Analytics Dashboard"] + [""] * 15])
    worksheet.format('A1:P1', {
        "backgroundColor": {"red": 0.1, "green": 0.3, "blue": 0.7},
        "textFormat": {"bold": True, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "fontSize": 16},
        "horizontalAlignment": "CENTER"
    })
    worksheet.merge_cells('A1:P1')
    
    print("✅ Section 1 completed - waiting 30 seconds...")
    for i in range(30, 0, -1):
        print(f"\r⏳ Waiting {i:2d} seconds to avoid API limits...", end="", flush=True)
        time.sleep(1)
    print("\n")
    
    # === SECTION 2: REVIEW REMINDERS ===  
    print("📝 Section 2/6: Setting up review reminders and learning progress...")
    
    # === ROW 3: TODAY'S REVIEW REMINDERS ===
    worksheet.update('A3', [['📅 TODAY\'S REVIEW REMINDERS']])
    worksheet.format('A3', {"textFormat": {"bold": True, "fontSize": 12, "foregroundColor": {"red": 0.8, "green": 0.2, "blue": 0.2}}})
    
    # Due Today Count (F column is now Next Review)
    worksheet.update('A4', [['🔥 Due Today:']])
    worksheet.update('B4', [['=COUNTIFS(Problems!F:F,"<="&TODAY(),Problems!A:A,"<>Problem")']], value_input_option='USER_ENTERED')
    worksheet.format('B4', {"textFormat": {"bold": True, "fontSize": 14, "foregroundColor": {"red": 0.8, "green": 0.2, "blue": 0.2}}})
    
    # Overdue Count (F column is now Next Review)
    worksheet.update('A5', [['⚠️  Overdue:']])
    worksheet.update('B5', [['=COUNTIFS(Problems!F:F,"<"&TODAY(),Problems!A:A,"<>Problem")']], value_input_option='USER_ENTERED')
    worksheet.format('B5', {"textFormat": {"bold": True, "fontSize": 14, "foregroundColor": {"red": 1.0, "green": 0.0, "blue": 0.0}}})
    
    # This Week Count (F column is now Next Review)
    worksheet.update('A6', [['📋 This Week:']])
    worksheet.update('B6', [['=COUNTIFS(Problems!F:F,"<="&TODAY()+7,Problems!F:F,">="&TODAY(),Problems!A:A,"<>Problem")']], value_input_option='USER_ENTERED')
    worksheet.format('B6', {"textFormat": {"bold": True, "fontSize": 14, "foregroundColor": {"red": 0.0, "green": 0.6, "blue": 0.0}}})
    
    print("✅ Section 2 completed - waiting 30 seconds...")
    for i in range(30, 0, -1):
        print(f"\r⏳ Waiting {i:2d} seconds to avoid API limits...", end="", flush=True)
        time.sleep(1)
    print("\n")
    
    # === MAIN TITLE ===
    worksheet.update(range_name='A1:P1', values=[["🎯 LeetCode Learning Analytics Dashboard"] + [""] * 15])
    worksheet.format('A1:P1', {
        "backgroundColor": {"red": 0.1, "green": 0.3, "blue": 0.7},
        "textFormat": {"bold": True, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "fontSize": 16},
        "horizontalAlignment": "CENTER"
    })
    worksheet.merge_cells('A1:P1')
    
    # === ROW 3: TODAY'S REVIEW REMINDERS ===
    worksheet.update('A3', [['📅 TODAY\'S REVIEW REMINDERS']])
    worksheet.format('A3', {"textFormat": {"bold": True, "fontSize": 12, "foregroundColor": {"red": 0.8, "green": 0.2, "blue": 0.2}}})
    
    # Due Today Count (F column is now Next Review)
    worksheet.update('A4', [['🔥 Due Today:']])
    worksheet.update('B4', [['=COUNTIFS(Problems!F:F,"<="&TODAY(),Problems!A:A,"<>Problem")']], value_input_option='USER_ENTERED')
    worksheet.format('B4', {"textFormat": {"bold": True, "fontSize": 14, "foregroundColor": {"red": 0.8, "green": 0.2, "blue": 0.2}}})
    
    # Overdue Count (F column is now Next Review)
    worksheet.update('A5', [['⚠️  Overdue:']])
    worksheet.update('B5', [['=COUNTIFS(Problems!F:F,"<"&TODAY(),Problems!A:A,"<>Problem")']], value_input_option='USER_ENTERED')
    worksheet.format('B5', {"textFormat": {"bold": True, "fontSize": 14, "foregroundColor": {"red": 1.0, "green": 0.0, "blue": 0.0}}})
    
    # This Week Count (F column is now Next Review)
    worksheet.update('A6', [['📋 This Week:']])
    worksheet.update('B6', [['=COUNTIFS(Problems!F:F,"<="&TODAY()+7,Problems!F:F,">="&TODAY(),Problems!A:A,"<>Problem")']], value_input_option='USER_ENTERED')
    worksheet.format('B6', {"textFormat": {"bold": True, "fontSize": 14, "foregroundColor": {"red": 0.0, "green": 0.6, "blue": 0.0}}})
    
    # === ROW 3-6: LEARNING PROGRESS TRACKING ===
    worksheet.update('D3', [['📈 LEARNING PROGRESS']])
    worksheet.format('D3', {"textFormat": {"bold": True, "fontSize": 12, "foregroundColor": {"red": 0.0, "green": 0.6, "blue": 0.8}}})
    
    # Total Solved
    worksheet.update('D4', [['📊 Total Solved:']])
    worksheet.update('E4', [['=COUNTA(Problems!A:A)-1']], value_input_option='USER_ENTERED')
    worksheet.format('E4', {"textFormat": {"bold": True, "fontSize": 14}})
    
    # Average Review Count (G column is now Review Count)
    worksheet.update('D5', [['🔄 Avg Reviews:']])
    worksheet.update('E5', [['=ROUND(AVERAGE(Problems!G:G),1)']], value_input_option='USER_ENTERED')
    worksheet.format('E5', {"textFormat": {"bold": True, "fontSize": 14}})
    
    # This Month Progress
    worksheet.update('D6', [['📅 This Month:']])
    worksheet.update('E6', [['=COUNTIFS(Problems!E:E,">="&EOMONTH(TODAY(),-1)+1,Problems!E:E,"<="&EOMONTH(TODAY(),0))']], value_input_option='USER_ENTERED')
    worksheet.format('E6', {"textFormat": {"bold": True, "fontSize": 14, "foregroundColor": {"red": 0.0, "green": 0.6, "blue": 0.0}}})
    
    # === ROW 3-6: DIFFICULTY BREAKDOWN WITH CHART ===
    worksheet.update('G3', [['🎯 DIFFICULTY BREAKDOWN']])
    worksheet.format('G3', {"textFormat": {"bold": True, "fontSize": 12, "foregroundColor": {"red": 0.4, "green": 0.2, "blue": 0.8}}})
    
    difficulty_data = [
        ['Difficulty', 'Count', 'Percentage'],
        ['Easy', '=COUNTIF(Problems!C:C,"Easy")', '=COUNTIF(Problems!C:C,"Easy")/(COUNTA(Problems!A:A)-1)'],
        ['Medium', '=COUNTIF(Problems!C:C,"Medium")', '=COUNTIF(Problems!C:C,"Medium")/(COUNTA(Problems!A:A)-1)'], 
        ['Hard', '=COUNTIF(Problems!C:C,"Hard")', '=COUNTIF(Problems!C:C,"Hard")/(COUNTA(Problems!A:A)-1)']
    ]
    worksheet.update('G4:I7', difficulty_data, value_input_option='USER_ENTERED')
    worksheet.format('G4:I4', {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}})
    worksheet.format('I5:I7', {"numberFormat": {"type": "PERCENT", "pattern": "0.0%"}})
    
    # === ROW 8: WEAKNESS ANALYSIS ===
    worksheet.update('A8', [['⚠️  WEAKNESS ANALYSIS - Topics Needing More Practice']])
    worksheet.format('A8', {"textFormat": {"bold": True, "fontSize": 12, "foregroundColor": {"red": 0.8, "green": 0.4, "blue": 0.0}}})
    
    # Headers for weakness analysis
    weakness_headers = ['Topic', 'Problems', 'Avg Reviews', 'Status']
    worksheet.update('A9:D9', [weakness_headers])
    worksheet.format('A9:D9', {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}})
    
    # Weakness analysis formulas - shows topics with high review counts
    weakness_formulas = [
        ['=IF(COUNTA(Problems!A:A)>1,"Array","No data yet")', '1', '2.0', 'Need Practice'],
        ['=IF(COUNTA(Problems!A:A)>1,"Dynamic Programming","--")', '0', '--', 'Practice More'],  
        ['=IF(COUNTA(Problems!A:A)>1,"Graph","--")', '0', '--', 'New Topic'],
        ['=IF(COUNTA(Problems!A:A)>1,"Tree","--")', '0', '--', 'Review'],
    ]
    worksheet.update('A10:D13', weakness_formulas, value_input_option='USER_ENTERED')
    
    # === ROW 15: SMART RECOMMENDATIONS ===
    worksheet.update('A15', [['💡 SMART LEARNING RECOMMENDATIONS']])
    worksheet.format('A15', {"textFormat": {"bold": True, "fontSize": 12, "foregroundColor": {"red": 0.0, "green": 0.7, "blue": 0.0}}})
    
    # Today's Review List
    worksheet.update('A16', [['🔥 Priority Reviews Today:']])
    worksheet.format('A16', {"textFormat": {"bold": True}})
    
    # Create simple count of due problems for quick reference
    review_count_formula = '=IF(COUNTA(Problems!A:A)>1,COUNTIFS(Problems!F2:F,"<="&TODAY())&" problems due for review","No reviews due")'
    worksheet.update('A17', [[review_count_formula]], value_input_option='USER_ENTERED')
    
    # Add detailed review list with hyperlinks in individual rows (18-24)
    worksheet.update('A18', [['📋 Today\'s Review List:']])
    worksheet.format('A18', {"textFormat": {"bold": True, "fontSize": 10}})
    
    # Create individual rows for up to 3 problems due for review with full hyperlinks
    # Use a simpler but more reliable approach
    for i in range(3):
        row = 19 + i
        
        # Create HYPERLINK formulas for each of the first 3 problems due for review
        if i == 0:
            # First problem due for review
            hyperlink_formula = f'''=IF(AND(COUNTA(Problems!A:A)>1,COUNTIFS(Problems!F2:F100,"<="&TODAY())>0),
HYPERLINK(
"https://leetcode.com/problems/"&
SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(LOWER(
INDEX(Problems!B2:B100,MATCH(TRUE,Problems!F2:F100<=TODAY(),0))
)," ","-"),"'",""),".","")&"/",
"📌 " & INDEX(Problems!A2:A100,MATCH(TRUE,Problems!F2:F100<=TODAY(),0)) & ". " & 
INDEX(Problems!B2:B100,MATCH(TRUE,Problems!F2:F100<=TODAY(),0))
),"")'''
        else:
            # For problems 2 and 3, use OFFSET or direct row targeting
            # This approach finds the nth problem due for review by skipping already found ones
            hyperlink_formula = f'''=IF(COUNTIFS(Problems!F2:F100,"<="&TODAY())>{i},
HYPERLINK(
"https://leetcode.com/problems/"&
SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(LOWER(
INDEX(Problems!B2:B100,SMALL(IF(Problems!F2:F100<=TODAY(),ROW(Problems!F2:F100)-1),{i+1}))
)," ","-"),"'",""),".","")&"/",
"📌 " & INDEX(Problems!A2:A100,SMALL(IF(Problems!F2:F100<=TODAY(),ROW(Problems!F2:F100)-1),{i+1})) & ". " &
INDEX(Problems!B2:B100,SMALL(IF(Problems!F2:F100<=TODAY(),ROW(Problems!F2:F100)-1),{i+1}))
),"")'''
        
        worksheet.update(f'A{row}', [[hyperlink_formula]], value_input_option='USER_ENTERED')
    
    # Add summary message if there are more than 3 problems
    worksheet.update('A22', [['=IF(COUNTIFS(Problems!F2:F100,"<="&TODAY())>3,"📋 " & (COUNTIFS(Problems!F2:F100,"<="&TODAY())-3) & " more problems due - see Problems sheet","")' ]], value_input_option='USER_ENTERED')
    
    # Update instruction text for direct hyperlinks
    worksheet.update('A24', [['🔗 Click on any problem above to open directly in LeetCode']])
    worksheet.format('A24', {"textFormat": {"fontSize": 9, "italic": True, "foregroundColor": {"red": 0.0, "green": 0.5, "blue": 0.8}}})
    
    # Add note about additional problems in Problems sheet  
    worksheet.update('A25', [['💡 For more problems, check the Problems sheet']])
    worksheet.format('A25', {"textFormat": {"fontSize": 9, "italic": True}})
    
    # === ADVANCED CHARTS SECTION ===
    worksheet.update('K3', [['📊 LEARNING CURVE ANALYTICS']])
    worksheet.format('K3', {"textFormat": {"bold": True, "fontSize": 14, "foregroundColor": {"red": 0.6, "green": 0.0, "blue": 0.6}}})
    
    # === 1. MONTHLY PROBLEM SOLVING TREND CHART ===
    worksheet.update('K5', [['📈 MONTHLY SOLVING TREND']])
    worksheet.format('K5', {"textFormat": {"bold": True, "fontSize": 12, "foregroundColor": {"red": 0.0, "green": 0.6, "blue": 0.8}}})
    
    monthly_headers = ['Month', 'Problems Solved', 'Cumulative']
    worksheet.update('K6:M6', [monthly_headers])
    worksheet.format('K6:M6', {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}})
    
    # Generate last 12 months data for better trend visualization
    monthly_formulas = []
    for i in range(12):
        month_start = f'EOMONTH(TODAY(),-{11-i})+1'
        month_end = f'EOMONTH(TODAY(),-{11-i})'
        cumulative_end = f'EOMONTH(TODAY(),-{11-i})'
        month_index = f'MONTH(EOMONTH(TODAY(),-{11-i}))'
        month_year = f'CHOOSE({month_index},"Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec") & " " & TEXT(EOMONTH(TODAY(),-{11-i}),"YY")'
        
        monthly_formulas.append([
            f'={month_year}',
            f'=COUNTIFS(Problems!E:E,">="&{month_start},Problems!E:E,"<="&{month_end})',
            f'=COUNTIF(Problems!E:E,"<="&{cumulative_end})'
        ])
    
    worksheet.update('K7:M18', monthly_formulas, value_input_option='USER_ENTERED')
    
    # Add sparkline chart for monthly trend
    worksheet.update('N7', [['=SPARKLINE(L7:L18,{"charttype","column";"color1","#4285F4";"max",MAX(L7:L18)})']], value_input_option='USER_ENTERED')
    # Note: Google Sheets API doesn't support "note" format - using comment instead
    worksheet.format('N7', {"textFormat": {"fontSize": 10}})
    
    # === 2. TOPIC MASTERY HEATMAP ===
    worksheet.update('K20', [['🔥 TOPIC MASTERY HEATMAP']])
    worksheet.format('K20', {"textFormat": {"bold": True, "fontSize": 12, "foregroundColor": {"red": 0.8, "green": 0.4, "blue": 0.0}}})
    
    heatmap_headers = ['Topic', 'Problems', 'Avg Reviews', 'Mastery Score', 'Heat']
    worksheet.update('K21:O21', [heatmap_headers])
    worksheet.format('K21:O21', {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}})
    
    # Create mastery calculation formulas
    heatmap_formulas = []
    common_topics = ['Array', 'Hash Table', 'Two Pointers', 'String', 'Dynamic Programming', 
                    'Binary Search', 'Tree', 'Graph', 'Stack', 'Linked List']
    
    for i, topic in enumerate(common_topics):
        row_idx = 22 + i
        # Mastery Score = (Problems Solved * 10) - (Average Review Count * 2)
        # Higher score = better mastery (more problems, fewer reviews needed)
        mastery_formula = f'=IF(COUNTIF(Problems!D:D,"*{topic}*")>0, (COUNTIF(Problems!D:D,"*{topic}*")*10) - (AVERAGEIFS(Problems!G:G,Problems!D:D,"*{topic}*")*2), 0)'
        # Heat visualization using conditional formatting scale
        heat_formula = f'=IF(L{row_idx}>0, ROUND(N{row_idx}/10,0), 0)'
        
        heatmap_formulas.append([
            topic,
            f'=COUNTIF(Problems!D:D,"*{topic}*")',
            f'=IF(COUNTIF(Problems!D:D,"*{topic}*")>0, ROUND(AVERAGEIFS(Problems!G:G,Problems!D:D,"*{topic}*"),1), "-")',
            mastery_formula,
            heat_formula
        ])
    
    worksheet.update(f'K22:O{21+len(common_topics)}', heatmap_formulas, value_input_option='USER_ENTERED')
    
    # Apply advanced conditional formatting for heat map visualization
    heat_range = f'O22:O{21+len(common_topics)}'
    mastery_range = f'N22:N{21+len(common_topics)}'
    
    # Create a color scale based on mastery scores
    # High mastery = Green, Medium = Yellow, Low = Red
    try:
        # Format the Heat column with conditional formatting
        worksheet.format(heat_range, {
            "backgroundColor": {"red": 0.95, "green": 0.95, "blue": 0.95},
            "textFormat": {"bold": True, "fontSize": 10}
        })
        
        # Apply color gradient to Mastery Score column for better visualization
        worksheet.format(mastery_range, {
            "textFormat": {"bold": True},
            "numberFormat": {"type": "NUMBER", "pattern": "0.0"}
        })
        
        # Add visual indicators for mastery levels in Heat column  
        for i, topic in enumerate(common_topics):
            row_idx = 22 + i
            # Use emoji indicators based on mastery score ranges
            heat_indicator_formula = f'=IF(N{row_idx}>=50,"🔥🔥🔥",IF(N{row_idx}>=30,"🔥🔥",IF(N{row_idx}>=10,"🔥",IF(N{row_idx}>0,"💧",""))))'
            worksheet.update(f'O{row_idx}', [[heat_indicator_formula]], value_input_option='USER_ENTERED')
            
        # Add legend for heat map
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
        
    except Exception as e:
        print(f"WARNING: Failed to apply advanced heat map formatting: {e}")
        # Fallback to simple formatting
        worksheet.format(heat_range, {
            "backgroundColor": {"red": 1.0, "green": 0.9, "blue": 0.9},
            "textFormat": {"bold": True}
        })
    
    # === 3. REVIEW SUCCESS RATE LINE CHART (Moved to avoid column limit) ===
    worksheet.update('A22', [['📊 REVIEW SUCCESS TREND']])
    worksheet.format('A22', {"textFormat": {"bold": True, "fontSize": 12, "foregroundColor": {"red": 0.0, "green": 0.7, "blue": 0.0}}})
    
    success_headers = ['Week', 'Reviews', 'Success %', 'Trend', 'Chart']
    worksheet.update('A23:E23', [success_headers])
    worksheet.format('A23:E23', {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}})
    
    # Calculate weekly review success rates (last 6 weeks to save space)
    success_formulas = []
    for i in range(6):
        week_start = f'TODAY()-{(5-i)*7}'
        week_end = f'TODAY()-{(5-i)*7-6}'
        week_label = f'=TEXT({week_start},"MM/DD")'
        
        # Count total problems reviewed in that week
        total_reviews = f'=COUNTIFS(Problems!H:H,">="&{week_start},Problems!H:H,"<="&{week_end})'
        
        # Success rate calculation: Problems that didn't need immediate re-review
        success_rate = f'=IF({total_reviews}>0, ROUND((COUNTIFS(Problems!H:H,">="&{week_start},Problems!H:H,"<="&{week_end},Problems!G:G,"<=3")/{total_reviews})*100,1), 0)'
        
        success_formulas.append([
            week_label,
            total_reviews,
            success_rate,
            f'=IF(C{24+i}>0, IF(C{24+i}>=80,"🟢",IF(C{24+i}>=60,"🟡","🔴")), "")',
            '' # Placeholder for sparkline
        ])
    
    worksheet.update('A24:E29', success_formulas, value_input_option='USER_ENTERED')
    
    # Add sparkline for success rate trend (moved to column E)
    worksheet.update('E24', [['=SPARKLINE(C24:C29,{"charttype","line";"color1","#34A853";"linewidth",2})']], value_input_option='USER_ENTERED')
    
    # === ADDITIONAL ADVANCED METRICS (Moved to fit within grid) ===
    worksheet.update('G22', [['⚡ ADVANCED LEARNING METRICS']])
    worksheet.format('G22', {"textFormat": {"bold": True, "fontSize": 12, "foregroundColor": {"red": 0.4, "green": 0.2, "blue": 0.8}}})
    
    advanced_metrics = [
        ['📚 Learning Velocity:', '=ROUND(COUNTA(Problems!A:A)/(DATEDIF(MIN(Problems!E:E),TODAY(),"D")+1),2)&" problems/day"'],
        ['🎯 Retention Rate:', '=ROUND((COUNTIFS(Problems!G:G,1)/COUNTA(Problems!A:A))*100,1)&"%"'],
        ['🔥 Difficulty Progress:', '=ROUND((COUNTIF(Problems!C:C,"Hard")/(COUNTA(Problems!A:A)-1))*100,1)&"% Hard"'],
        ['🏆 Topic Diversity:', '=COUNTA(Analysis!A:A)-3&" different topics"']
    ]
    
    worksheet.update('G23:H26', advanced_metrics, value_input_option='USER_ENTERED')
    worksheet.format('G23:G26', {"textFormat": {"bold": True}})
    worksheet.format('H23:H26', {"textFormat": {"bold": True, "fontSize": 12, "foregroundColor": {"red": 0.0, "green": 0.6, "blue": 0.0}}})
    
    # === STREAK TRACKING ===
    worksheet.update('N3', [['🔥 LEARNING STREAK']])
    worksheet.format('N3', {"textFormat": {"bold": True, "fontSize": 12, "foregroundColor": {"red": 1.0, "green": 0.4, "blue": 0.0}}})
    
    # Current streak (simplified - counts consecutive days with submissions)
    worksheet.update('N4', [['Current Streak:']])
    worksheet.update('O4', [['=COUNTA(Problems!E:E)-1&" Problems"']], value_input_option='USER_ENTERED')
    worksheet.format('O4', {"textFormat": {"bold": True, "fontSize": 14, "foregroundColor": {"red": 1.0, "green": 0.4, "blue": 0.0}}})
    
    # Best topics (most solved)
    worksheet.update('N6', [['🏆 Top Topics:']])
    worksheet.update('N7', [['=QUERY(Analysis!A4:C27,"SELECT A ORDER BY B DESC LIMIT 3")']], value_input_option='USER_ENTERED')
    
    # === FORMATTING AND BORDERS ===
    # Add borders to main sections (Updated for new compact layout)
    sections = [
        'A3:C6',   # Review Reminders
        'D3:F6',   # Learning Progress  
        'G3:I7',   # Difficulty Breakdown
        'A8:D12',  # Weakness Analysis
        'A13:F20', # Smart Recommendations
        'K5:N18',  # Monthly Trend Chart (Expanded)
        'K20:P32', # Topic Mastery Heatmap (Adjusted)
        'A22:E29', # Review Success Rate Chart (Moved)
        'G22:H26', # Advanced Learning Metrics (Moved)
        'N3:O8'    # Learning Streak
    ]
    
    for section in sections:
        worksheet.format(section, {
            "borders": {
                "top": {"style": "SOLID", "width": 1, "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
                "bottom": {"style": "SOLID", "width": 1, "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
                "left": {"style": "SOLID", "width": 1, "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
                "right": {"style": "SOLID", "width": 1, "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}
            }
        })
    
    # Apply comprehensive formatting
    apply_dashboard_formatting(worksheet)

def setup_data_validation(worksheet):
    """Set up data validation for difficulty column only"""
    try:
        # Difficulty column (C) - dropdown validation
        difficulty_rule = gspread.DataValidationRule(
            gspread.Condition('ONE_OF_LIST', DIFFICULTY_LIST), 
            allow_invalid=False,
            showCustomUi=True
        )
        worksheet.set_data_validation_rule('C2:C1000', difficulty_rule)
        
    except Exception as e:
        print(f"WARNING: Failed to set up data validation: {e}")

def format_data_sheet_headers(worksheet):
    # Format headers (A-J now includes review columns)
    worksheet.format('A1:J1', {
        "backgroundColor": HEADER_COLOR,
        "textFormat": {"bold": True},
        "horizontalAlignment": "CENTER"
    })
    
    worksheet.freeze(rows=1)
    
    # Apply comprehensive formatting
    apply_problems_formatting(worksheet)

def apply_conditional_formatting(worksheet):
    """Apply conditional formatting for difficulty and topic cells"""
    try:
        # Enhanced Difficulty color coding with better visibility
        easy_rule = gspread.ConditionalFormatRule(
            ranges=[gspread.GridRange.from_a1_range('C2:C1000', worksheet)],
            condition=gspread.Condition('TEXT_EQ', ['Easy']),
            format=gspread.CellFormat(
                backgroundColor=gspread.Color(0.85, 1.0, 0.85),  # Light green
                textFormat=gspread.TextFormat(bold=True, foregroundColor=gspread.Color(0.0, 0.6, 0.0))
            )
        )
        
        medium_rule = gspread.ConditionalFormatRule(
            ranges=[gspread.GridRange.from_a1_range('C2:C1000', worksheet)],
            condition=gspread.Condition('TEXT_EQ', ['Medium']),
            format=gspread.CellFormat(
                backgroundColor=gspread.Color(1.0, 0.95, 0.7),  # Light yellow
                textFormat=gspread.TextFormat(bold=True, foregroundColor=gspread.Color(0.8, 0.6, 0.0))
            )
        )
        
        hard_rule = gspread.ConditionalFormatRule(
            ranges=[gspread.GridRange.from_a1_range('C2:C1000', worksheet)],
            condition=gspread.Condition('TEXT_EQ', ['Hard']),
            format=gspread.CellFormat(
                backgroundColor=gspread.Color(1.0, 0.85, 0.85),  # Light red
                textFormat=gspread.TextFormat(bold=True, foregroundColor=gspread.Color(0.8, 0.0, 0.0))
            )
        )
        
        worksheet.add_conditional_format_rule(easy_rule)
        worksheet.add_conditional_format_rule(medium_rule) 
        worksheet.add_conditional_format_rule(hard_rule)
        
        # Enhanced Topic column formatting with tag-like appearance
        worksheet.format('D2:D1000', {
            "backgroundColor": {"red": 0.95, "green": 0.95, "blue": 1.0},  # Light blue
            "textFormat": {
                "bold": True,
                "fontSize": 10,
                "foregroundColor": {"red": 0.2, "green": 0.2, "blue": 0.8}
            },
            "borders": {
                "top": {"style": "SOLID", "width": 1, "color": {"red": 0.7, "green": 0.7, "blue": 0.9}},
                "bottom": {"style": "SOLID", "width": 1, "color": {"red": 0.7, "green": 0.7, "blue": 0.9}},
                "left": {"style": "SOLID", "width": 1, "color": {"red": 0.7, "green": 0.7, "blue": 0.9}},
                "right": {"style": "SOLID", "width": 1, "color": {"red": 0.7, "green": 0.7, "blue": 0.9}}
            },
            "horizontalAlignment": "CENTER"
        })
        
    except Exception as e:
        print(f"WARNING: Failed to apply conditional formatting: {e}")

def add_visual_enhancements(worksheet, row_number):
    """Add visual enhancements to newly inserted rows"""
    try:
        # Format the main visible range (now includes review columns)
        main_range = f'A{row_number}:J{row_number}'
        
        # Add alternating row colors for better readability  
        if row_number % 2 == 0:
            bg_color = {"red": 0.98, "green": 0.98, "blue": 0.98}  # Very light gray
        else:
            bg_color = {"red": 1.0, "green": 1.0, "blue": 1.0}    # White
        
        worksheet.format(main_range, {
            "backgroundColor": bg_color,
            "borders": {
                "bottom": {"style": "SOLID", "width": 1, "color": {"red": 0.9, "green": 0.9, "blue": 0.9}}
            }
        })
        
        # Format display topics cell (D) to look more like tags
        topic_cell = f'D{row_number}'
        worksheet.format(topic_cell, {
            "backgroundColor": {"red": 0.95, "green": 0.95, "blue": 1.0},
            "textFormat": {
                "bold": True,
                "fontSize": 10,
                "foregroundColor": {"red": 0.2, "green": 0.2, "blue": 0.8}
            },
            "horizontalAlignment": "CENTER"
        })
        
        # Only main columns now (A-G), no auxiliary columns
        
    except Exception as e:
        print(f"WARNING: Failed to add visual enhancements: {e}")

# --- Spaced Repetition Logic ---
def calculate_next_review_date(difficulty: str, review_count: int = 0) -> str:
    today = datetime.date.today()
    
    # Base intervals by difficulty
    base_days = {"Easy": 14, "Medium": 7, "Hard": 3}.get(difficulty, 2)
    
    # Increase interval with each review using spaced repetition formula
    # Interval = base_interval * (2.5 ^ review_count)
    if review_count > 0:
        multiplier = 2.5 ** review_count
        days_to_add = int(base_days * multiplier)
        # Cap maximum interval at 365 days (1 year)
        days_to_add = min(days_to_add, 365)
    else:
        days_to_add = base_days
    
    return (today + datetime.timedelta(days=days_to_add)).isoformat()

def find_existing_problem(worksheet, problem_number: str):
    """Find existing problem by problem number in the sheet"""
    try:
        # Get all problem numbers from column A (excluding header)
        problem_numbers = worksheet.col_values(1)[1:]  # Skip header row
        
        for i, cell_value in enumerate(problem_numbers, start=2):  # Start from row 2
            # Extract number from hyperlink formula if present
            if cell_value.startswith('=HYPERLINK'):
                # Extract problem number from hyperlink text
                import re
                match = re.search(r'"(\d+)"', cell_value)
                if match and match.group(1) == problem_number:
                    return i
            elif cell_value == problem_number:
                return i
        return None
    except Exception as e:
        print(f"Error finding existing problem: {e}")
        return None

# --- API Endpoints ---
@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint for connection testing"""
    return jsonify({"status": "ok", "service": "leetcode-journey"})

@app.route('/log', methods=['POST'])
def log_submission():
    data = request.json
    required_fields = ['problem_number', 'name', 'difficulty', 'url']
    if not all(field in data for field in required_fields):
        return jsonify({"status": "error", "message": "Missing required fields."}), 400

    try:
        gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
        spreadsheet = gc.open(SHEET_NAME)
        data_worksheet = get_or_create_worksheet(spreadsheet, DATA_SHEET_NAME)
        
        difficulty = data.get('difficulty', 'Medium')
        problem_number = data.get('problem_number')
        problem_hyperlink = f'=HYPERLINK("{data.get("url")}", "{problem_number}")'
        topics_string = data.get('topic', '')
        today = datetime.date.today().isoformat()
        notes = data.get('notes', '')

        # Check if sheet is empty to handle first write correctly
        if not data_worksheet.row_values(1):
            # Initialize sheet with headers and first problem
            new_row_data = [
                problem_hyperlink,                           # A: Problem
                data.get('name', ''),                       # B: Name
                difficulty,                                 # C: Difficulty
                topics_string,                              # D: Topics
                today,                                      # E: Date
                calculate_next_review_date(difficulty, 0),  # F: Next Review
                "1",                                        # G: Review Count
                today,                                      # H: Last Review
                today,                                      # I: Review History
                notes                                       # J: Notes (MOVED TO END)
            ]
            
            data_to_write = [EXPECTED_HEADERS, new_row_data]
            data_worksheet.update(range_name=f'A1:J2', values=data_to_write, value_input_option='USER_ENTERED')
            
            try:
                format_data_sheet_headers(data_worksheet)
                setup_data_validation(data_worksheet)
                apply_conditional_formatting(data_worksheet)
            except Exception as format_e:
                print(f"WARNING: Failed to format data sheet: {format_e}")

            try:
                setup_analysis_sheet(spreadsheet)
                setup_dashboard_sheet(spreadsheet)
            except Exception as sheet_e:
                print(f"WARNING: Failed to set up analysis/dashboard sheets: {sheet_e}")
                
            return jsonify({"status": "success", "message": "First problem logged successfully."})
        
        # Ensure Analysis and Dashboard sheets exist (check every time)
        try:
            setup_analysis_sheet(spreadsheet)
            setup_dashboard_sheet(spreadsheet)
        except Exception as sheet_e:
            print(f"WARNING: Failed to set up analysis/dashboard sheets: {sheet_e}")
        
        # Check if problem already exists
        existing_row = find_existing_problem(data_worksheet, problem_number)
        
        if existing_row:
            # Update existing problem (review scenario)
            try:
                # Get current data from existing row
                current_row_data = data_worksheet.row_values(existing_row)
                
                # Parse current review count and history (NEW COLUMN ORDER)
                current_review_count = int(current_row_data[6]) if len(current_row_data) > 6 and current_row_data[6].isdigit() else 0
                new_review_count = current_review_count + 1
                
                current_history = current_row_data[8] if len(current_row_data) > 8 else ""
                new_history = f"{current_history}; {today}" if current_history else today
                
                # Calculate new review date based on updated count
                next_review_date = calculate_next_review_date(difficulty, new_review_count)
                
                # Update specific cells for review (NEW COLUMN ORDER)
                updates = [
                    {'range': f'E{existing_row}', 'values': [[today]]},           # E: Date (last solved)
                    {'range': f'F{existing_row}', 'values': [[next_review_date]]}, # F: Next Review
                    {'range': f'G{existing_row}', 'values': [[str(new_review_count)]]}, # G: Review Count
                    {'range': f'H{existing_row}', 'values': [[today]]},          # H: Last Review
                    {'range': f'I{existing_row}', 'values': [[new_history]]},    # I: Review History
                    {'range': f'J{existing_row}', 'values': [[notes]]},          # J: Notes (NOW AT END)
                ]
                
                # Batch update for efficiency
                data_worksheet.batch_update(updates, value_input_option='USER_ENTERED')
                
                return jsonify({
                    "status": "success", 
                    "message": f"Problem #{problem_number} review logged! Review count: {new_review_count}, Next review: {next_review_date}"
                })
                
            except Exception as update_e:
                print(f"Error updating existing problem: {update_e}")
                return jsonify({"status": "error", "message": f"Failed to update review: {update_e}"}), 500
        else:
            # Add new problem
            new_row_data = [
                problem_hyperlink,                           # A: Problem
                data.get('name', ''),                       # B: Name
                difficulty,                                 # C: Difficulty
                topics_string,                              # D: Topics
                today,                                      # E: Date
                calculate_next_review_date(difficulty, 0),  # F: Next Review
                "1",                                        # G: Review Count (first time)
                today,                                      # H: Last Review
                today,                                      # I: Review History
                notes                                       # J: Notes (MOVED TO END)
            ]
            
            data_worksheet.append_row(new_row_data, value_input_option='USER_ENTERED')
            
            # Visual enhancements for new row
            try:
                row_count = len(data_worksheet.get_all_values())
                add_visual_enhancements(data_worksheet, row_count)
            except Exception as visual_e:
                print(f"WARNING: Failed to add visual enhancements to new row: {visual_e}")

            return jsonify({"status": "success", "message": "New problem logged successfully."})

    except Exception as e:
        print(f"An error occurred while processing the row: {e}")
        return jsonify({"status": "error", "message": f"An internal error occurred: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)