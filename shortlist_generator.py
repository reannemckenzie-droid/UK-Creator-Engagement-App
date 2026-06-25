import gspread
import pandas as pd
import google.auth
from datetime import datetime
import re

def get_gspread_client():
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    credentials, project = google.auth.default(scopes=scopes)
    return gspread.authorize(credentials)

def find_column_index(headers, targets):
    """Finds the index of a column that matches one of the target names."""
    for target in targets:
        try:
            return [h.lower().strip() for h in headers].index(target.lower().strip())
        except ValueError:
            continue
    return -1

def get_submissions_worksheet(sh, name):
    """Attempts to find the submissions worksheet by name or alternatives."""
    try:
        return sh.worksheet(name)
    except:
        alternatives = ['Form Responses 1', 'Form_Submissions', 'Submissions', 'Requests']
        for alt in alternatives:
            try:
                return sh.worksheet(alt)
            except:
                continue
    return None

def get_available_submissions(spreadsheet_url, submissions_sheet_name):
    """Returns a list of recent submissions and the worksheet title found."""
    try:
        gc = get_gspread_client()
        sh = gc.open_by_url(spreadsheet_url)
        sub_ws = get_submissions_worksheet(sh, submissions_sheet_name)
        
        if not sub_ws:
            available = [w.title for w in sh.worksheets()]
            return None, f"Could not find submissions worksheet. Available sheets: {', '.join(available)}"
        
        all_rows = sub_ws.get_all_records()
        if not all_rows:
            return [], sub_ws.title
            
        # Return last 20 submissions for selection
        return all_rows[-20:], sub_ws.title
    except Exception as e:
        return None, str(e)

def generate_shortlist(spreadsheet_url, database_sheet_name, submissions_sheet_name, selected_submission=None):
    try:
        gc = get_gspread_client()
        sh = gc.open_by_url(spreadsheet_url)
        
        # 1. Get the submission to process
        if selected_submission:
            last_submission = selected_submission
        else:
            sub_ws = get_submissions_worksheet(sh, submissions_sheet_name)
            if not sub_ws:
                available = [w.title for w in sh.worksheets()]
                return f"Error: Could not find submissions worksheet. Available sheets: {', '.join(available)}", None
            
            submissions = sub_ws.get_all_records()
            if not submissions:
                return "No submissions found in the request form sheet.", None
            last_submission = submissions[-1]
        
        # Identify creator name column in submissions
        creator_col_candidates = ['Creator Name', 'Channel Name', 'Which creator is this for?', 'Creator', 'Channel']
        creator_name = None
        submission_headers = list(last_submission.keys())
        
        for cand in creator_col_candidates:
            match = next((k for k in submission_headers if cand.lower() in k.lower()), None)
            if match:
                creator_name = str(last_submission[match]).strip()
                break
        
        if not creator_name or creator_name.lower() == 'n/a':
            return f"Could not identify a valid creator name in the submission. Found: {creator_name}", None

        # 2. Search for creator in the main database
        try:
            db_ws = sh.worksheet(database_sheet_name)
        except Exception:
            available = [w.title for w in sh.worksheets()]
            return f"Error: Could not find database worksheet '{database_sheet_name}'. Available: {', '.join(available)}", None
        
        # Get headers B1:AG2
        headers_data = db_ws.get('B1:AG2')
        all_db_values = db_ws.get_all_values()
        
        if len(all_db_values) < 2:
            return "Database sheet is empty.", None
            
        db_header_row = all_db_values[1] # Row 2
        col_channel_name_candidates = ['Channel Name', 'channel name', 'Channel']
        db_col_idx = find_column_index(db_header_row, col_channel_name_candidates)
        
        if db_col_idx == -1:
            db_col_idx = find_column_index(all_db_values[0], col_channel_name_candidates)
            
        if db_col_idx == -1:
            return f"Could not find 'Channel Name' column in database.", None

        # Filter rows
        matched_rows = []
        for row in all_db_values[2:]:
            if len(row) > db_col_idx and row[db_col_idx].strip().lower() == creator_name.lower():
                padded_row = row + [''] * (33 - len(row))
                matched_rows.append(padded_row[1:33])
                
        if not matched_rows:
            return f"No records found for creator '{creator_name}' in the database.", None

        # 3. Create the new shortlist spreadsheet
        new_sh_title = f"Shortlist - {creator_name} - {datetime.now().strftime('%Y%m%d_%H%M')}"
        new_sh = gc.create(new_sh_title)
        new_ws = new_sh.get_worksheet(0)
        new_ws.update_title("Shortlist")
        
        # 4. Populate with headers and matched rows
        new_ws.update('A1', headers_data)
        new_ws.update('A3', matched_rows)
        new_ws.format('A1:AF2', {'textFormat': {'bold': True}})
        
        # 5. Share
        requester_email_candidates = ['Email', 'Email Address', 'Requester Email', 'Your Email']
        requester_email = None
        for cand in requester_email_candidates:
            match = next((k for k in submission_headers if cand.lower() in k.lower()), None)
            if match:
                requester_email = str(last_submission[match]).strip()
                if '@' in requester_email:
                    break
                else:
                    requester_email = None
        
        share_msg = ""
        if requester_email:
            try:
                new_sh.share(requester_email, perm_type='user', role='writer', notify=True)
                share_msg = f" and shared with {requester_email}"
            except Exception as e:
                share_msg = f" (Failed to share with {requester_email}: {str(e)})"

        return f"Successfully created shortlist for '{creator_name}'!{share_msg}", new_sh.url

    except Exception as e:
        return f"An unexpected error occurred: {str(e)}", None
