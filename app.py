import streamlit as st
import pandas as pd
import gspread
import google.auth
from google.auth.transport.requests import Request
from google.oauth2 import service_account
import re
import json
import requests
from shortlist_generator import generate_shortlist

# --- 2. AUTHENTICATION ---
# 1. Pull your secret key from the Streamlit vault
try:
    if "gcp_key" in st.secrets:
        creds_data = st.secrets["gcp_key"]
        
        # Handle cases where secrets might be a dict already or a string
        if isinstance(creds_data, str):
            creds_dict = json.loads(creds_data)
        else:
            creds_dict = dict(creds_data)

        # Use a broader scope for better compatibility with User Credentials/ADC
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        
        # Detect type and load accordingly
        if creds_dict.get("type") == "service_account":
            credentials = service_account.Credentials.from_service_account_info(creds_dict, scopes=scopes)
            email = creds_dict.get("client_email", "Unknown Service Account")
            st.sidebar.success(f"✅ Service Account Loaded: {email}")
        else:
            # Fallback for "authorized_user" type (like from ADC)
            import google.oauth2.credentials
            credentials = google.oauth2.credentials.Credentials.from_authorized_user_info(creds_dict, scopes=scopes)
            email = creds_dict.get("account", "Unknown User")
            st.sidebar.success(f"✅ User Credentials Loaded: {email}")
    else:
        credentials = None
        st.sidebar.warning("⚠️ No gcp_key found in secrets.")
except Exception as e:
    credentials = None
    st.sidebar.error(f"❌ Credential Loading Error: {e}")

def get_gspread_client():
    if credentials:
        return gspread.authorize(credentials)
    
    # Fallback to Application Default Credentials (ADC)
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds, project = google.auth.default(scopes=scopes)
    return gspread.authorize(creds)

# --- 1. CONFIG & BRANDING ---
st.set_page_config(page_title="UK Creator Engagement", layout="wide")

# YouTube Aesthetic CSS Injection
st.markdown("""
    <style>
    /* Main Background & Text */
    .stApp { background-color: #FFFFFF; }
    h1, h2, h3 { color: #0F0F0F !important; font-family: 'YouTube Sans', sans-serif; font-weight: 700; }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] { background-color: #0F0F0F; color: white; }
    [data-testid="stSidebar"] * { color: white !important; }
    
    /* YouTube Red Buttons */
    div.stButton > button {
        background-color: #FF0000;
        color: white;
        border-radius: 20px;
        border: none;
        padding: 10px 24px;
        font-weight: bold;
    }
    
    /* Creator Card Styling */
    .creator-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        border: 1px solid #f0f0f0;
        margin-bottom: 20px;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        display: block;
    }
    
    .creator-card:hover {
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
        transform: translateY(-5px);
        border-color: #FF0000; /* Subtle YouTube Red accent */
    }

    /* Style adjustments for elements inside the card */
    .creator-card h3 { margin-top: 10px; margin-bottom: 5px; }
    .creator-card p { font-size: 0.9rem; color: #606060; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR NAVIGATION & CONFIG ---
st.sidebar.title("UK Creator Engagement")
page = st.sidebar.radio("Navigation", ["Browse Creators", "UK Creator Requests"])
st.sidebar.divider()

# Move the text input up so SPREADSHEET_URL exists first
with st.sidebar.expander("Admin Configuration"):
    SPREADSHEET_URL = st.text_input(
        "Google Sheet URL", 
        "https://docs.google.com/spreadsheets/d/1wRUj7D5XhJJptRk4XzN84TnP01bovtLHy010EeHjXUk/edit?resourcekey=0-EdAPbTcONZTkWuJ46XHyzw&gid=349889363#gid=349889363"
    )

# Now safely initialize the client with the variable the user provides
try:
    gc = get_gspread_client()
    sh_init = gc.open_by_url(SPREADSHEET_URL) # Pass the actual variable, not temp_url
    all_worksheets = [w.title for w in sh_init.worksheets()]
except Exception as e:
    all_worksheets = ["H1 2026 Database", "UK Creator Request Form"]

# Build selectboxes out here using the freshly fetched worksheet array
with st.sidebar.expander("Admin Configuration"):
    db_default_idx = all_worksheets.index("H1 2026 Database") if "H1 2026 Database" in all_worksheets else 0
    DATABASE_SHEET = st.selectbox("Database Worksheet", all_worksheets, index=db_default_idx)
    
    sub_default_idx = all_worksheets.index("UK Creator Request Form") if "UK Creator Request Form" in all_worksheets else (1 if len(all_worksheets) > 1 else 0)
    SUBMISSIONS_SHEET = st.selectbox("Submissions Worksheet", all_worksheets, index=sub_default_idx)

@st.cache_data(show_spinner=False)
def get_yt_profile_pic(url):
    if not url or url == '#' or 'youtube.com' not in url:
        return None
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
        response = requests.get(url, timeout=5, headers=headers)
        if response.status_code == 200:
            # Look for og:image
            match = re.search(r'<meta property="og:image" content="([^"]+)">', response.text)
            if match:
                return match.group(1)
            # Fallback to twitter:image
            match = re.search(r'<meta name="twitter:image" content="([^"]+)">', response.text)
            if match:
                return match.group(1)
    except:
        pass
    return None

try:
    # We already have gc from the initial connection above
    sh = gc.open_by_url(SPREADSHEET_URL)
except Exception as e:
    st.sidebar.error(f"Spreadsheet Access Failed: {e}")
    st.info("Double-check that the Spreadsheet URL is correct and that the account you used to generate the key has access to it.")
    st.stop()

# --- 4. PAGE 1: BROWSE CREATORS ---
if page == "Browse Creators":
    st.title("UK Creator Engagement")
    
    # Load Data
    try:
        worksheet = sh.worksheet('H1 2026 Database')
    except:
        # Fallback to case-insensitive search for worksheet
        worksheet_names = [w.title for w in sh.worksheets()]
        ws_match = next((n for n in worksheet_names if n.lower().strip() == 'h1 2026 database'), 'H1 2026 Database')
        worksheet = sh.worksheet(ws_match)
        
    data = pd.DataFrame(worksheet.get_all_records(head=2))

    # Identify primary columns with case-insensitive matching
    def find_col(df, targets):
        for target in targets:
            match = next((c for c in df.columns if c.lower().strip() == target.lower()), None)
            if match: return match
        return targets[0]

    col_channel_name = find_col(data, ['Channel Name', 'channel name'])
    col_subscribers = find_col(data, ['Subscriber Count', 'Subscribers', 'Channel Subs (Channel Level)'])
    col_bio = find_col(data, ['Bio', 'Creator Bio'])
    col_link = find_col(data, ['Channel Link', 'Channel URL'])
    col_img = find_col(data, ['YouTube Profile Picture', 'Image URL', 'Photo URL'])
    vertical_col = find_col(data, ['Specific Vertical', 'Vertical'])

    # Helper to parse subscriber counts for sorting
    def parse_subs(sub_count):
        try:
            val = str(sub_count).upper().strip().replace(',', '')
            multiplier = 1
            if 'M' in val:
                multiplier = 1_000_000
                val = val.replace('M', '')
            elif 'K' in val:
                multiplier = 1_000
                val = val.replace('K', '')
            return float(re.sub(r'[^\d.]', '', val)) * multiplier
        except:
            return 0.0

    data['subs_numeric'] = data[col_subscribers].apply(parse_subs)

    # Filter out metadata rows and ensure only rows with a Channel Name are processed
    exclude_list = [
        "Original Source",
        "[FYIO] Gemini prompt used to retrieve the info",
        "[For SPMs] Description for validation of each column",
        "YouTube",
        "📺 View Channel",
        "👥 YouTube Subscribers",
        "Gemini",
        "N/A",
        "👥 N/A Subscribers",
        "What is the person in Column S is best known for",
        "What is the creator best known for"
    ]
    
    # Ensure Channel Name column exists and has content
    filtered_creators = data[data[col_channel_name].astype(str).str.strip().ne('')]
    
    # Exclude metadata from the main list
    filtered_creators = filtered_creators[~filtered_creators[col_channel_name].astype(str).str.contains('|'.join([re.escape(x) for x in exclude_list]), case=False, na=False)]

    # Filter Controls
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    with col_filter1:
        search_query = st.text_input("Search Creators:", placeholder="Search by name, category, or bio...")
    
    with col_filter2:
        if vertical_col in data.columns:
            # User requested to ignore cells L3, L4, and L5 (indices 0, 1, 2)
            vertical_data_for_filter = data.drop([0, 1, 2]) if len(data) > 3 else data
            available_verticals = ["All"] + sorted([str(v) for v in vertical_data_for_filter[vertical_col].unique() if v and str(v) not in exclude_list])
        else:
            available_verticals = ["All"]
        selected_vertical = st.selectbox("Filter by Category:", available_verticals)

    with col_filter3:
        sort_option = st.selectbox("Sort by Subscribers:", ["Default", "Smallest to Largest", "Largest to Smallest"])
    
    # Apply Vertical Filter
    if selected_vertical != "All":
        filtered_creators = filtered_creators[filtered_creators[vertical_col] == selected_vertical]

    # Apply Search Logic
    if search_query:
        query = search_query.lower()
        search_mask = (
            filtered_creators[col_channel_name].astype(str).str.lower().str.contains(query) |
            filtered_creators[vertical_col].astype(str).str.lower().str.contains(query) |
            filtered_creators[col_bio].astype(str).str.lower().str.contains(query)
        )
        final_creators = filtered_creators[search_mask]
        
        if final_creators.empty:
            st.warning(f"Not found: '{search_query}'")
            import difflib
            # Get suggestions from all possible searchable fields
            all_terms = filtered_creators[col_channel_name].unique().tolist() + \
                        filtered_creators[vertical_col].unique().tolist()
            suggestions = difflib.get_close_matches(query, [str(x) for x in all_terms if x], n=5, cutoff=0.3)
            if suggestions:
                st.info(f"Did you mean: {', '.join(set(suggestions))}?")
            filtered_creators = final_creators # Still empty
        else:
            filtered_creators = final_creators

    # Sorting
    if sort_option == "Smallest to Largest":
        filtered_creators = filtered_creators.sort_values(by='subs_numeric', ascending=True)
    elif sort_option == "Largest to Smallest":
        filtered_creators = filtered_creators.sort_values(by='subs_numeric', ascending=False)

    # Display Uniform Grid
    def format_subs(sub_count):
        try:
            # Clean and normalize input
            val = str(sub_count).upper().strip().replace(',', '')
            
            # Identify multiplier
            multiplier = 1
            if 'M' in val:
                multiplier = 1_000_000
                val = val.replace('M', '')
            elif 'K' in val:
                multiplier = 1_000
                val = val.replace('K', '')
            
            # Extract numeric part
            num = float(re.sub(r'[^\d.]', '', val)) * multiplier
            
            # Format based on size
            if num >= 1_000_000:
                return f"{num / 1_000_000:.1f}M"
            elif num >= 1_000:
                return f"{num / 1_000:.1f}K"
            else:
                return f"{num:.1f}"
        except:
            return str(sub_count)

    # Use container for grid to ensure alignment
    grid_container = st.container()
    
    # Define columns per row
    COLS_PER_ROW = 3
    
    rows = [filtered_creators.iloc[i:i+COLS_PER_ROW] for i in range(0, len(filtered_creators), COLS_PER_ROW)]

    for row_data in rows:
        cols = st.columns(COLS_PER_ROW)
        for i, (idx, creator) in enumerate(row_data.iterrows()):
            with cols[i]:
                # Get data with fallbacks for flexible sheet headers
                channel_name = creator.get(col_channel_name, 'N/A')
                subscribers = format_subs(creator.get(col_subscribers, '0'))
                bio = creator.get(col_bio, 'No bio available.')
                channel_link = creator.get(col_link, '#')
                
                # Use the profile picture from creators youtube channel url
                yt_img = get_yt_profile_pic(channel_link)
                image_url = yt_img if yt_img else creator.get(col_img, 'https://via.placeholder.com/150')

                # Sleek Creator Card UI
                st.markdown(f"""
                <div class="creator-card">
                    <img src="{image_url}" style="width:100%; border-radius:10px; margin-bottom:15px; height: 180px; object-fit: contain; background-color: #f8f9fa;">
                    <h3 style="margin:0; font-size: 1.1rem; min-height: 2.5em; line-height: 1.2;">{channel_name}</h3>
                    <p style="margin-bottom:5px; font-size: 0.9rem;">
                        <a href="{channel_link}" target="_blank" style="color:#FF0000; font-weight:bold; text-decoration:none;">📺 {channel_name}</a>
                    </p>
                    <p style="margin-bottom:10px;">👥 <b>{subscribers}</b> Subscribers</p>
                    <div style="font-size:0.85rem; color:#606060; background:#f9f9f9; padding:10px; border-radius:8px; min-height: 80px; max-height: 80px; overflow: hidden;">
                        {bio}
                    </div>
                </div>
                """, unsafe_allow_html=True)

# --- 5. PAGE 2: UK CREATOR REQUESTS ---
elif page == "UK Creator Requests":
    st.title("UK Creator Requests")
    
    st.markdown("### 📥 Submit New Request")
    st.link_button("Open Google Campaign Form", "https://docs.google.com/forms/d/e/1FAIpQLSel6354_mdG88FlKC7qSiuD3S7p74oQiOw1NCipAeRTdABfOg/viewform", type="primary")
    st.markdown("Want more details on the UK Creator Request Process go to: [go/ukcreatorengagement](http://go/ukcreatorengagement)")
    
    st.divider()
    
    st.subheader("🔒 Admin: Automate Shortlist")
    
    user_email = "placeholder@example.com" # We'll fix this to be dynamic later
    authorized_users = ["your-email@example.com", "admin1@example.com", "placeholder@example.com"]
    
    if user_email in authorized_users:
        st.success("Access Granted: Admin Mode")
        
        # --- TASK #3: THE AUTOMATION GAP ---
        if st.button("Generate Shortlist from Last Submission"):
            with st.spinner("Analyzing last submission and generating shortlist..."):
                message, url = generate_shortlist(SPREADSHEET_URL, DATABASE_SHEET, SUBMISSIONS_SHEET)
                if url:
                    st.success(message)
                    st.link_button("View New Shortlist", url)
                else:
                    st.error(message)
    else:
        st.warning("This section is restricted to authorized personnel.")
