import streamlit as st
from PIL import Image
import requests
from io import BytesIO
import time
from collection_log_randomizer import get_random_collection_log_item, scrape_collection_log

# Set page config
st.set_page_config(
    page_title="OSRS Collection Log Randomizer",
    page_icon="🎲",
    layout="centered"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main {
        background-color: #2b2b2b;
        color: #ffffff;
    }
    .item-card {
        background-color: #3c3c3c;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        border: 1px solid #555;
    }
    .item-name {
        font-size: 24px;
        font-weight: bold;
        color: #ffd700;
    }
    .item-source {
        font-size: 18px;
        color: #aaaaaa;
    }
    .item-category {
        font-size: 16px;
        color: #aaaaaa;
        font-style: italic;
    }
    .source-list {
        margin-top: 10px;
        padding: 10px;
        background-color: #333;
        border-radius: 5px;
    }
    .st-emotion-cache-1kyxreq {
        display: flex;
        justify-content: center;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for the current item
if 'current_item' not in st.session_state:
    st.session_state.current_item = None

# Preload data function to avoid loading on each reroll
@st.cache_resource
def load_collection_log_data():
    """Load collection log data and cache it"""
    return scrape_collection_log()

# Function to download and display image
def display_item_image(image_url):
    try:
        if not image_url:
            return None
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))
        return img
    except Exception as e:
        st.error(f"Error loading image: {e}")
        return None

# Main app
st.title("OSRS Collection Log Randomizer")
st.markdown("Generate a random item from Old School RuneScape's Collection Log!")

# Load the data
with st.spinner("Loading collection log data..."):
    data = load_collection_log_data()
    st.success(f"Loaded {len(data['unique_items'])} unique items from {len(data['items'])} total collection log slots")

# Roll button
if st.button("🎲 Roll for Random Collection Log Item", use_container_width=True):
    with st.spinner("Rolling..."):
        # Add small delay for dramatic effect
        time.sleep(0.5)
        st.session_state.current_item = get_random_collection_log_item(include_duplicates=False)

# Display item if available
if st.session_state.current_item:
    item = st.session_state.current_item
    
    st.markdown("<div class='item-card'>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        img = display_item_image(item["icon"])
        if img:
            st.image(img, width=80)
    
    with col2:
        st.markdown(f"<p class='item-name'>{item['name']}</p>", unsafe_allow_html=True)
        
        if 'sources' in item and len(item['sources']) > 0:
            # Get primary source
            primary_source = item['sources'][0]
            st.markdown(f"<p class='item-source'>Source: {primary_source['subcategory']}</p>", unsafe_allow_html=True)
            st.markdown(f"<p class='item-category'>Category: {primary_source['category']}</p>", unsafe_allow_html=True)
            
            # If there are multiple sources, show them all
            if len(item['sources']) > 1:
                st.markdown("<div class='source-list'>", unsafe_allow_html=True)
                st.markdown(f"This item appears in {len(item['sources'])} places:")
                for source in item['sources']:
                    st.markdown(f"- {source['category']} > {source['subcategory']}")
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            # Fallback for items without sources
            st.markdown(f"<p class='item-source'>Source: {item['subcategory']}</p>", unsafe_allow_html=True)
            st.markdown(f"<p class='item-category'>Category: {item['category']}</p>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# Run the app with: streamlit run app.py 