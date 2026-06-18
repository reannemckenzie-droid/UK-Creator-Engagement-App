import streamlit as st
import pandas as pd
import re
import requests

# --- 1. CONFIG & BRANDING ---
st.set_page_config(page_title="Preview: Creator Engagement", layout="wide")

@st.cache_data(show_spinner=False)
def get_yt_profile_pic(url):
    if not url or url == '#' or 'youtube.com' not in url:
        return None
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
        response = requests.get(url, timeout=5, headers=headers)
        if response.status_code == 200:
            match = re.search(r'<meta property="og:image" content="([^"]+)">', response.text)
            if match: return match.group(1)
            match = re.search(r'<meta name="twitter:image" content="([^"]+)">', response.text)
            if match: return match.group(1)
    except: pass
    return None

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

# --- 2. MOCK DATA ---
mock_data = [
    {"Channel Name": "TechReviewUK", "Subscriber Count": "1.2M", "Vertical": "Gaming", "Bio": "In-depth reviews of the latest gaming hardware and peripherals.", "YouTube Profile Picture": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=400", "Channel Link": "https://youtube.com"},
    {"Channel Name": "LondonLooks", "Subscriber Count": "850K", "Vertical": "Lifestyle", "Bio": "Exploring the best fashion and lifestyle trends across London.", "YouTube Profile Picture": "https://images.unsplash.com/photo-1529139513055-07f909ef3c5c?w=400", "Channel Link": "https://youtube.com"},
    {"Channel Name": "PitchSide", "Subscriber Count": "2.1M", "Vertical": "Football", "Bio": "Weekly analysis of Premier League matches and transfer news.", "YouTube Profile Picture": "https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=400", "Channel Link": "https://youtube.com"},
    {"Channel Name": "KitchenCanvas", "Subscriber Count": "500K", "Vertical": "Lifestyle", "Bio": "Modern British recipes with a focus on seasonal ingredients.", "YouTube Profile Picture": "https://images.unsplash.com/photo-1556910103-1c02745aae4d?w=400", "Channel Link": "https://youtube.com"},
    {"Channel Name": "GreenGrip", "Subscriber Count": "300K", "Vertical": "Golf", "Bio": "Pro tips for improving your short game and course vlogs.", "YouTube Profile Picture": "https://images.unsplash.com/photo-1535131749006-b7f58c99034b?w=400", "Channel Link": "https://youtube.com"},
    {"Channel Name": "SpeedStreet", "Subscriber Count": "1.5M", "Vertical": "Sports", "Bio": "Everything F1 and endurance racing coverage.", "YouTube Profile Picture": "https://images.unsplash.com/photo-1533130061792-64b345e4a833?w=400", "Channel Link": "https://youtube.com"}
]
data = pd.DataFrame(mock_data)

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

data['subs_numeric'] = data['Subscriber Count'].apply(parse_subs)

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.title("🇬🇧 Engagement Hub")
page = st.sidebar.radio("Navigation", ["Browse Creators", "Request Campaign"])

# --- 4. PAGE 1: BROWSE CREATORS ---
if page == "Browse Creators":
    st.title("UK Creator Engagement (Preview Mode)")
    st.subheader("Specific Content Vertical")
    
    # Selection Grid for Verticals
    verticals = ["All", "Lifestyle", "Gaming", "Sports", "Football", "Golf"]
    
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        selected_vertical = st.selectbox("Filter by Category:", verticals)
    with col_filter2:
        sort_option = st.selectbox("Sort by Subscribers:", ["Default", "Smallest to Largest", "Largest to Smallest"])
    
    # Filtering Logic
    if selected_vertical == "All":
        filtered_creators = data
    else:
        filtered_creators = data[data['Vertical'] == selected_vertical]

    # Apply sorting
    if sort_option == "Smallest to Largest":
        filtered_creators = filtered_creators.sort_values(by='subs_numeric', ascending=True)
    elif sort_option == "Largest to Smallest":
        filtered_creators = filtered_creators.sort_values(by='subs_numeric', ascending=False)

    # Display Grid
    cols = st.columns(3)
    
    def format_subs(sub_count):
        try:
            val = str(sub_count).upper().strip().replace(',', '')
            multiplier = 1
            if 'M' in val:
                multiplier = 1_000_000
                val = val.replace('M', '')
            elif 'K' in val:
                multiplier = 1_000
                val = val.replace('K', '')
            num = float(re.sub(r'[^\d.]', '', val)) * multiplier
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
            channel_name = creator.get('Channel Name', 'N/A')
            subscribers = format_subs(creator.get('Subscriber Count', '0'))
            bio = creator.get('Bio', 'No bio available.')
            channel_link = creator.get('Channel Link', '#')
            
            # Use the profile picture from creators youtube channel url
            yt_img = get_yt_profile_pic(channel_link)
            image_url = yt_img if yt_img else creator.get('YouTube Profile Picture', 'https://via.placeholder.com/150')

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

elif page == "Request Campaign":
    st.title("Campaign Command Center")
    st.markdown("### 📥 Submit New Request")
    st.link_button("Open Google Campaign Form", "https://forms.google.com/your-form-link", type="primary")
