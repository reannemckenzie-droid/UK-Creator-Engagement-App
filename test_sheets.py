import google.auth
import gspread
import sys

def test_auth():
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    try:
        credentials, project = google.auth.default(scopes=scopes)
        print(f"Project: {project}")
        print(f"Credentials Type: {type(credentials)}")
        
        gc = gspread.authorize(credentials)
        url = "https://docs.google.com/spreadsheets/d/1wRUj7D5XhJJptRk4XzN84TnP01bovtLHy010EeHjXUk/edit"
        sh = gc.open_by_url(url)
        print("Success! Opened spreadsheet.")
        print(f"Title: {sh.title}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_auth()
