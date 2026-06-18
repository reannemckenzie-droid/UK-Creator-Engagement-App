import streamlit as st
import pandas as pd
import gspread
import google.auth
from google.auth.transport.requests import Request
import re
import requests

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

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.title("UK Creator Engagement")
page = st.sidebar.radio("Navigation", ["Browse Creators", "Creator Engagement Request"])

st.sidebar.divider()
st.sidebar.subheader("Configuration")
SPREADSHEET_URL = st.sidebar.text_input(
    "Google Sheet URL", 
    "https://docs.google.com/spreadsheets/d/1wRUj7D5XhJJptRk4XzN84TnP01bovtLHy010EeHjXUk/edit?resourcekey=0-EdAPbTcONZTkWuJ46XHyzw&gid=349889363#gid=349889363"
)

# --- 2. AUTHENTICATION (ADC) ---
def get_gspread_client():
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    credentials, project = google.auth.default(scopes=scopes)
    return gspread.authorize(credentials)

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
    gc = get_gspread_client()
    sh = gc.open_by_url(SPREADSHEET_URL)
except Exception as e:
    st.sidebar.error("Authentication or Spreadsheet Access Failed.")
    st.info("Ensure you have run 'gcloud auth application-default login' and the spreadsheet is shared correctly.")
    st.stop()

# --- 4. PAGE 1: BROWSE CREATORS ---
if page == "Browse Creators":
    st.title("UK Creator Engagement")
    st.subheader("Specific Content Vertical")
    
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

    # Filter out metadata rows that shouldn't appear as creator cards
    exclude_list = [
        "Original Source",
        "[FYIO] Gemini prompt used to retrieve the info",
        "[For SPMs] Description for validation of each column"
    ]
    name_cols = ['Creator Name', 'Name', col_channel_name]
    for col in name_cols:
        if col in data.columns:
            data = data[~data[col].astype(str).str.contains('|'.join([re.escape(x) for x in exclude_list]), case=False, na=False)]

    # Selection Grid for Verticals
    vertical_col = find_col(data, ['Specific Vertical', 'Vertical'])
    if vertical_col in data.columns:
        available_verticals = ["All"] + sorted([str(v) for v in data[vertical_col].unique() if v])
    else:
        available_verticals = ["All"]
    
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        selected_vertical = st.selectbox("Filter by Category:", available_verticals)
    with col_filter2:
        sort_option = st.selectbox("Sort by Subscribers:", ["Default", "Smallest to Largest", "Largest to Smallest"])
    
    # --- TASK #2: FILTERING LOGIC ---
    if selected_vertical == "All":
        filtered_creators = data
    else:
        filtered_creators = data[data[vertical_col] == selected_vertical]

    # Apply sorting
    if sort_option == "Smallest to Largest":
        filtered_creators = filtered_creators.sort_values(by='subs_numeric', ascending=True)
    elif sort_option == "Largest to Smallest":
        filtered_creators = filtered_creators.sort_values(by='subs_numeric', ascending=False)

    # Display Grid
    cols = st.columns(3)

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

    for index, (idx, creator) in enumerate(filtered_creators.iterrows()):
        with cols[index % 3]:
            # Get data with fallbacks for flexible sheet headers
            channel_name = creator.get(col_channel_name, 'N/A')
            subscribers = format_subs(creator.get(col_subscribers, '0'))
            bio = creator.get(col_bio, 'No bio available.')
            channel_link = creator.get(col_link, '#')
            
            # Use the profile picture from creators youtube channel url
            yt_img = get_yt_profile_pic(channel_link)
            image_url = yt_img if yt_img else creator.get(col_img, 'https://via.placeholder.com/150')

            # Sleek Creator Card UI (Previous Format)
            st.markdown(f"""
            <div class="creator-card">
                <img src="{image_url}" style="width:100%; border-radius:10px; margin-bottom:15px; height: 150px; object-fit: cover;">
                <h3 style="margin:0;">{channel_name}</h3>
                <p style="margin-bottom:5px;">
                    <a href="{channel_link}" target="_blank" style="color:#FF0000; font-weight:bold; text-decoration:none;">📺 {channel_name}</a>
                </p>
                <p style="margin-bottom:10px;">👥 <b>{subscribers}</b> Subscribers</p>
                <div style="font-size:0.85rem; color:#606060; background:#f9f9f9; padding:10px; border-radius:8px; min-height: 60px;">
                    {bio}
                </div>
            </div>
            """, unsafe_allow_html=True)

# --- 5. PAGE 2: REQUEST CAMPAIGN ---
elif page == "Request Campaign":
    st.title("Campaign Command Center")
    
    st.markdown("### 📥 Submit New Request")
    st.link_button("Open Google Campaign Form", "https://docs.google.com/forms/d/e/1FAIpQLSel6354_mdG88FlKC7qSiuD3S7p74oQiOw1NCipAeRTdABfOg/viewform", type="primary")
    
    st.divider()
    
    st.subheader("🔒 Admin: Automate Shortlist")
    
    user_email = "placeholder@example.com" # We'll fix this to be dynamic later
    authorized_users = ["your-email@example.com", "admin1@example.com"]
    
    if user_email in authorized_users:
        st.success("Access Granted: Admin Mode")
        
        # --- TASK #3: THE AUTOMATION GAP ---
        # Logic: Read 'Form_Submissions', match with 'Project_Atlas', save to 'Active_Shortlists'
        if st.button("Generate Shortlist from Last Submission"):
            st.write("Processing... (This is where your magic code goes!)")
    else:
        st.warning("This section is restricted to authorized personnel.")
