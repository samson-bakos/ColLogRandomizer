import streamlit as st
from PIL import Image
import requests
from io import BytesIO
import time
import json
import random
import os
import shutil
from collection_log_randomizer import get_random_collection_log_item, scrape_collection_log, get_item_by_id
from temple_api import TempleApi
from item_lookup_service import get_item

# Set page config
st.set_page_config(
    page_title="OSRS Collection Log Randomizer",
    page_icon="🎲",
    layout="centered"
)

# Cache file from collection_log_randomizer
CACHE_FILE = "collection_log_data.json"

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
    .temple-info {
        background-color: #394053;
        border: 1px solid #4a5568;
        border-radius: 5px;
        padding: 15px;
        margin-top: 10px;
    }
    .collection-status {
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 15px;
        background-color: #333;
        border-left: 4px solid #ffd700;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if 'current_item' not in st.session_state:
    st.session_state.current_item = None
if 'temple_api' not in st.session_state:
    st.session_state.temple_api = TempleApi()
if 'rsn' not in st.session_state:
    st.session_state.rsn = ""
if 'temple_data' not in st.session_state:
    st.session_state.temple_data = None
if 'debug_info' not in st.session_state:
    st.session_state.debug_info = {}
if 'available_unowned_items' not in st.session_state:
    st.session_state.available_unowned_items = []

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

# Function to get collection log status from Temple API
def get_collection_log_status(rsn, force_refresh=False):
    """Get collection log status for a player"""
    # Check if we need to refresh the data
    if force_refresh or not st.session_state.temple_data or st.session_state.rsn != rsn:
        with st.spinner("Fetching collection log data from TempleOSRS..."):
            temple_api = st.session_state.temple_api
            data = temple_api.get_collection_log(rsn, force_refresh)
            st.session_state.temple_data = data
            st.session_state.rsn = rsn
            
            # If data is valid and not an error, preload all unowned items
            if "error" not in data:
                preload_unowned_items(rsn)
    else:
        data = st.session_state.temple_data
    
    # Return the data
    return data

# Function to preload all unowned items
def preload_unowned_items(rsn):
    """Preload and cache all unowned item details"""
    with st.spinner("Loading your unowned collection log items..."):
        try:
            # Get all unowned IDs
            temple_api = st.session_state.temple_api
            unowned_ids = temple_api.get_unowned_items(rsn)
            
            if not unowned_ids:
                st.warning("No unowned items found in your collection log.")
                st.session_state.available_unowned_items = []
                return
            
            st.session_state.debug_info["unowned_count"] = len(unowned_ids)
            st.session_state.debug_info["unowned_sample"] = unowned_ids[:5] if unowned_ids else []
            
            # Look up all items in parallel
            available_items = []
            looked_up_items = []
            
            # Load local collection log data once to avoid repeated calls
            local_data = load_collection_log_data()["unique_items"]
            
            # Create a name-based lookup dictionary to speed up matching
            local_items_by_name = {}
            for item in local_data:
                name = item.get("name", "").lower()
                if name:
                    local_items_by_name[name] = item
            
            # Create progress bar
            progress_text = "Looking up items..."
            progress_bar = st.progress(0, text=progress_text)
            total_items = len(unowned_ids)
            
            # Process all unowned IDs
            for i, item_id in enumerate(unowned_ids):
                # Update progress
                progress_percent = int((i / total_items) * 100)
                progress_bar.progress(progress_percent / 100, text=f"{progress_text} ({i}/{total_items})")
                
                # Look up item details
                item_details = get_item(item_id)
                if item_details:
                    # Create an item object in the format expected by our app
                    looked_up_item = {
                        "id": int(item_id),
                        "name": item_details["name"],
                        "category": "Unknown",  # We don't have category info
                        "subcategory": "Unknown",
                        "icon": item_details["icon"],
                        "sources": [{
                            "category": "Temple Mode",
                            "subcategory": "Unowned Item"
                        }]
                    }
                    
                    looked_up_items.append(looked_up_item)
                    
                    # Try to match with our local item database for better category info
                    item_name_lower = item_details["name"].lower()
                    if item_name_lower in local_items_by_name:
                        # If we found a local match, use that instead for better data
                        available_items.append(local_items_by_name[item_name_lower])
                    else:
                        # Otherwise use our looked up item
                        available_items.append(looked_up_item)
            
            # Complete progress bar and remove it
            progress_bar.progress(1.0, text="Completed!")
            # Wait a moment to let users see the completed progress bar, then clear it
            time.sleep(0.5)
            progress_bar.empty()
            
            # Store in session state
            st.session_state.available_unowned_items = available_items
            
            # Update debug info
            st.session_state.debug_info["available_items_count"] = len(available_items)
            st.session_state.debug_info["looked_up_items_count"] = len(looked_up_items)
            
            # Remove success message - just continue silently
            
        except Exception as e:
            st.error(f"Error loading unowned items: {e}")
            st.session_state.available_unowned_items = []

# Function to get a random unowned collection log item using Temple API
def get_temple_mode_item(rsn):
    """Get a random unowned collection log item based on player data from TempleOSRS"""
    # Get collection log data
    data = get_collection_log_status(rsn)
    
    # Check if there was an error
    if "error" in data:
        error_message = data.get("error")
        if isinstance(error_message, dict) and "Code" in error_message and error_message.get("Code") == 402:
            # Show special message for sync issue
            st.error("Your collection log hasn't been synced with TempleOSRS yet.")
            st.markdown("""
            <div class="temple-info">
            <h4>How to sync your collection log with TempleOSRS:</h4>
            <ol>
            <li>Visit <a href="https://templeosrs.com/" target="_blank">TempleOSRS</a> and create an account</li>
            <li>Follow their instructions to connect your RuneScape account</li>
            <li>Once synced, return here and try again</li>
            </ol>
            <p>In the meantime, we'll use Regular Mode to select a random item from all collection log items.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Show generic error
            st.error(f"Error connecting to TempleOSRS: {error_message}")
            
        # Fall back to regular mode
        return get_random_collection_log_item(include_duplicates=False)
    
    # Check if we have available unowned items
    if not st.session_state.available_unowned_items:
        st.warning("No unowned items found or couldn't fetch data from Temple OSRS. Using random item selection.")
        return get_random_collection_log_item(include_duplicates=False)
    
    # Simply return a random item from our preloaded list
    return random.choice(st.session_state.available_unowned_items)

# Main app
st.title("OSRS Collection Log Randomizer")
st.markdown("Generate a random item from Old School RuneScape's Collection Log!")

# Load the data silently, without showing the success message
with st.spinner("Loading collection log data..."):
    data = load_collection_log_data()
    # Success message removed

# Add mode selection
mode = st.radio("Select Mode", ["Regular", "Temple Mode"], horizontal=True)

# If Temple Mode, add RSN input and display collection status
rsn = ""
if mode == "Temple Mode":
    # Simplified layout without columns - just a single input field
    rsn = st.text_input("Enter RuneScape Name (RSN):", value=st.session_state.rsn)
    
    # If we have an RSN, fetch and display collection log status
    if rsn:
        # Fetch data (without refresh button)
        temple_data = get_collection_log_status(rsn, force_refresh=False)
        
        # Display collection log status if available
        if "error" not in temple_data and "data" in temple_data:
            data = temple_data["data"]
            if "total_collections_finished" in data and "total_collections_available" in data:
                finished = data["total_collections_finished"]
                total = data["total_collections_available"]
                
                # Calculate completion percentage
                completion_pct = round((int(finished) / int(total)) * 100, 2)
                
                # Display collection log status
                st.markdown(f"""
                <div class="collection-status">
                    <h3>Collection Log Status</h3>
                    <p>You have collected <b>{finished}/{total}</b> items ({completion_pct}%)</p>
                    <p>Items remaining: <b>{int(total) - int(finished)}</b></p>
                </div>
                """, unsafe_allow_html=True)

# Roll button
roll_button = st.button("🎲 Roll for Random Collection Log Item", use_container_width=True)
if roll_button:
    with st.spinner("Rolling..."):
        # Add small delay for dramatic effect
        time.sleep(0.5)
        
        # Get item based on mode
        if mode == "Regular":
            st.session_state.current_item = get_random_collection_log_item(include_duplicates=False)
        else:  # Temple Mode
            if not rsn:
                st.error("Please enter a RuneScape Name (RSN) to use Temple Mode.")
            else:
                st.session_state.current_item = get_temple_mode_item(rsn)
                # Save RSN for next time
                st.session_state.rsn = rsn

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