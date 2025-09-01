import os
import gspread
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import functions_framework

# Load environment variables
load_dotenv()

# Import all functions from app.py to maintain compatibility
from app import (
    get_or_create_worksheet,
    setup_analysis_sheet,
    setup_dashboard_sheet,
    setup_data_validation,
    format_data_sheet_headers,
    apply_conditional_formatting,
    add_visual_enhancements,
    calculate_next_review_date,
    find_existing_problem,
    EXPECTED_HEADERS,
    SERVICE_ACCOUNT_FILE,
    SHEET_NAME,
    DATA_SHEET_NAME
)

# For Cloud Functions, we need to handle the credentials differently
# Check if running in Cloud Functions environment
if os.getenv('K_SERVICE'):  # Cloud Functions environment variable
    # In Cloud Functions, we'll use environment variables for service account
    import json
    from google.oauth2 import service_account
    
    # Get credentials from environment variable
    credentials_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
    if credentials_json:
        import base64
        # Decode base64 encoded JSON
        decoded_json = base64.b64decode(credentials_json).decode('utf-8')
        credentials_info = json.loads(decoded_json)
        # Create credentials with proper scopes
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=[
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
        )
        # Override the gspread auth method
        gc = gspread.authorize(credentials)
    else:
        # Fallback to service account file
        gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
else:
    # Local development - use service account file
    gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)

# Create Flask app for Cloud Functions
app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["chrome-extension://*", "http://127.0.0.1:*", "https://*.cloudfunctions.net"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint for connection testing"""
    return jsonify({"status": "ok", "service": "leetcode-journey"})

@app.route('/log', methods=['POST'])
def log_submission():
    """Cloud Functions compatible endpoint"""
    data = request.json
    required_fields = ['problem_number', 'name', 'difficulty', 'url']
    if not all(field in data for field in required_fields):
        return jsonify({"status": "error", "message": "Missing required fields."}), 400

    try:
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
                notes                                       # J: Notes
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
        
        # Ensure Analysis and Dashboard sheets exist
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
                current_row_data = data_worksheet.row_values(existing_row)
                
                current_review_count = int(current_row_data[6]) if len(current_row_data) > 6 and current_row_data[6].isdigit() else 0
                new_review_count = current_review_count + 1
                
                current_history = current_row_data[8] if len(current_row_data) > 8 else ""
                new_history = f"{current_history}; {today}" if current_history else today
                
                next_review_date = calculate_next_review_date(difficulty, new_review_count)
                
                updates = [
                    {'range': f'E{existing_row}', 'values': [[today]]},
                    {'range': f'F{existing_row}', 'values': [[next_review_date]]},
                    {'range': f'G{existing_row}', 'values': [[str(new_review_count)]]},
                    {'range': f'H{existing_row}', 'values': [[today]]},
                    {'range': f'I{existing_row}', 'values': [[new_history]]},
                    {'range': f'J{existing_row}', 'values': [[notes]]},
                ]
                
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
                "1",                                        # G: Review Count
                today,                                      # H: Last Review
                today,                                      # I: Review History
                notes                                       # J: Notes
            ]
            
            data_worksheet.append_row(new_row_data, value_input_option='USER_ENTERED')
            
            try:
                row_count = len(data_worksheet.get_all_values())
                add_visual_enhancements(data_worksheet, row_count)
            except Exception as visual_e:
                print(f"WARNING: Failed to add visual enhancements to new row: {visual_e}")

            return jsonify({"status": "success", "message": "New problem logged successfully."})

    except Exception as e:
        print(f"An error occurred while processing the row: {e}")
        return jsonify({"status": "error", "message": f"An internal error occurred: {e}"}), 500

# Cloud Functions entry point
@functions_framework.http
def leetcode_journey(request):
    """Cloud Functions HTTP entry point"""
    try:
        # Handle CORS preflight requests
        if request.method == 'OPTIONS':
            headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '3600'
            }
            return ('', 204, headers)
        
        # Handle different paths
        if request.path == '/' or request.path == '':
            # Health check
            response = jsonify({"status": "ok", "service": "leetcode-journey"})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        elif request.path == '/log' or request.path.endswith('/log'):
            # Handle logging request
            if request.method != 'POST':
                return jsonify({"status": "error", "message": "Only POST method allowed"}), 405
            
            # Get JSON data
            try:
                data = request.get_json()
                if not data:
                    return jsonify({"status": "error", "message": "No JSON data provided"}), 400
            except Exception as json_e:
                return jsonify({"status": "error", "message": f"Invalid JSON: {json_e}"}), 400
            
            # Process the logging request (same logic as Flask route)
            required_fields = ['problem_number', 'name', 'difficulty', 'url']
            if not all(field in data for field in required_fields):
                return jsonify({"status": "error", "message": "Missing required fields."}), 400

            try:
                # Try to open existing spreadsheet, create if not found
                try:
                    spreadsheet = gc.open(SHEET_NAME)
                    print(f"Found existing spreadsheet: {SHEET_NAME}")
                except Exception as open_error:
                    print(f"Spreadsheet not found, creating new one: {SHEET_NAME}")
                    print(f"Open error details: {open_error}")
                    # Create new spreadsheet
                    spreadsheet = gc.create(SHEET_NAME)
                    print(f"Created new spreadsheet: {SHEET_NAME}")
                    
                    # Make the spreadsheet accessible to service account
                    try:
                        # Share with service account email for editing
                        service_email = credentials.service_account_email if hasattr(credentials, 'service_account_email') else 'cfunction@leetcode-joureny.iam.gserviceaccount.com'
                        spreadsheet.share(service_email, perm_type='user', role='writer')
                        print(f"Shared spreadsheet with service account: {service_email}")
                    except Exception as share_error:
                        print(f"Warning: Could not share spreadsheet: {share_error}")
                    
                data_worksheet = get_or_create_worksheet(spreadsheet, DATA_SHEET_NAME)
                
                difficulty = data.get('difficulty', 'Medium')
                problem_number = data.get('problem_number')
                problem_hyperlink = f'=HYPERLINK("{data.get("url")}", "{problem_number}")'
                topics_string = data.get('topic', '')
                today = datetime.date.today().isoformat()
                notes = data.get('notes', '')

                # Check if sheet is empty to handle first write correctly
                try:
                    first_row = data_worksheet.row_values(1)
                    is_empty = not first_row or len(first_row) == 0
                except Exception as row_error:
                    print(f"Error checking first row: {row_error}")
                    is_empty = True
                
                if is_empty:
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
                        notes                                       # J: Notes
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
                        
                    response = jsonify({"status": "success", "message": "First problem logged successfully."})
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response
                
                # Ensure Analysis and Dashboard sheets exist
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
                        current_row_data = data_worksheet.row_values(existing_row)
                        
                        current_review_count = int(current_row_data[6]) if len(current_row_data) > 6 and current_row_data[6].isdigit() else 0
                        new_review_count = current_review_count + 1
                        
                        current_history = current_row_data[8] if len(current_row_data) > 8 else ""
                        new_history = f"{current_history}; {today}" if current_history else today
                        
                        next_review_date = calculate_next_review_date(difficulty, new_review_count)
                        
                        updates = [
                            {'range': f'E{existing_row}', 'values': [[today]]},
                            {'range': f'F{existing_row}', 'values': [[next_review_date]]},
                            {'range': f'G{existing_row}', 'values': [[str(new_review_count)]]},
                            {'range': f'H{existing_row}', 'values': [[today]]},
                            {'range': f'I{existing_row}', 'values': [[new_history]]},
                            {'range': f'J{existing_row}', 'values': [[notes]]},
                        ]
                        
                        data_worksheet.batch_update(updates, value_input_option='USER_ENTERED')
                        
                        response = jsonify({
                            "status": "success", 
                            "message": f"Problem #{problem_number} review logged! Review count: {new_review_count}, Next review: {next_review_date}"
                        })
                        response.headers.add('Access-Control-Allow-Origin', '*')
                        return response
                        
                    except Exception as update_e:
                        print(f"Error updating existing problem: {update_e}")
                        error_message = str(update_e)
                        if '<Response [200]>' in error_message:
                            error_message = "Update completed but returned unexpected format. Please check your Google Sheet."
                        response = jsonify({"status": "error", "message": f"Failed to update review: {error_message}"})
                        response.headers.add('Access-Control-Allow-Origin', '*')
                        return response, 500
                else:
                    # Add new problem
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
                        notes                                       # J: Notes
                    ]
                    
                    data_worksheet.append_row(new_row_data, value_input_option='USER_ENTERED')
                    
                    try:
                        row_count = len(data_worksheet.get_all_values())
                        add_visual_enhancements(data_worksheet, row_count)
                    except Exception as visual_e:
                        print(f"WARNING: Failed to add visual enhancements to new row: {visual_e}")

                    response = jsonify({"status": "success", "message": "New problem logged successfully."})
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response

            except Exception as e:
                print(f"An error occurred while processing the row: {e}")
                import traceback
                print(f"Full traceback: {traceback.format_exc()}")
                error_message = str(e)
                if '<Response [200]>' in error_message:
                    error_message = "Google Sheets operation completed but returned unexpected format. Please check your Google Sheet manually."
                response = jsonify({"status": "error", "message": f"An internal error occurred: {error_message}"})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 500
        else:
            return jsonify({"status": "error", "message": "Endpoint not found"}), 404
            
    except Exception as e:
        print(f"Error in Cloud Function: {e}")
        return jsonify({"status": "error", "message": f"Cloud Function error: {e}"}), 500

if __name__ == '__main__':
    # Local development
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)