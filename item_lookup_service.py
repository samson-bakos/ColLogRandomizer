"""
Item Lookup Service for OSRS Collection Log Items

This module provides functions to look up OSRS items by their ID using the osrsreboxed database.
"""
import os
import json
import logging
from typing import Dict, Optional, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("item_lookup")

# Constants
CACHE_DIR = "item_cache"
CACHE_FILE = os.path.join(CACHE_DIR, "item_lookup_cache.json")

# Create cache directory if it doesn't exist
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# Global cache for items we've already looked up
item_cache = {}
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, 'r') as f:
            item_cache = json.load(f)
        logger.info(f"Loaded {len(item_cache)} items from cache")
    except Exception as e:
        logger.error(f"Error loading cache: {e}")

def save_cache():
    """Save the item cache to disk"""
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(item_cache, f, indent=2)
        logger.info(f"Saved {len(item_cache)} items to cache")
    except Exception as e:
        logger.error(f"Error saving cache: {e}")

def get_item(item_id: str) -> Optional[Dict[str, Any]]:
    """
    Get item details by ID from the osrsreboxed database
    
    Args:
        item_id: The numeric ID of the item to look up
        
    Returns:
        Dictionary with item details or None if not found
    """
    # Convert to string to ensure consistent cache keys
    item_id = str(item_id)
    
    # Check cache first
    if item_id in item_cache:
        logger.info(f"Cache hit for item {item_id}")
        return item_cache[item_id]
    
    logger.info(f"Looking up item with ID {item_id}")
    
    try:
        # Import here to avoid dependency issues if not installed
        from osrsreboxed import items_api
        
        # Load all items (this is cached internally)
        all_items = items_api.load()
        
        # Try to find the item by ID
        item = all_items.lookup_by_item_id(int(item_id))
        if not item:
            logger.info(f"Item {item_id} not found in osrsreboxed database")
            item_cache[item_id] = None
            save_cache()
            return None
            
        # Create a standardized item object
        result = {
            'id': str(item.id),
            'name': item.name,
            'examine': item.examine,
            'icon': f"https://raw.githubusercontent.com/0xNeffarion/osrsreboxed-db/master/items-icons/{item.id}.png",
            'members': item.members,
            'tradeable': item.tradeable,
            'wiki_url': item.wiki_url
        }
        
        # Cache the result
        item_cache[item_id] = result
        save_cache()
        return result
        
    except ImportError:
        logger.warning("osrsreboxed not installed. Use 'pip install osrsreboxed' to enable lookup.")
        return None
    except Exception as e:
        logger.error(f"Error looking up item {item_id} in osrsreboxed: {e}")
        return None

# Test function
def test_lookup():
    """Test the item lookup functionality"""
    # Sample of known items
    test_ids = ['13262', '13277', '22746', '30154', '29836', '29792']
    
    print("Testing item lookup:")
    for item_id in test_ids:
        print(f"\nLooking up item ID: {item_id}")
        item = get_item(item_id)
        if item:
            print(f"✅ SUCCESS: {item['name']}")
            print(f"   Icon URL: {item['icon']}")
            print(f"   Examine: {item['examine']}")
            print(f"   Wiki URL: {item.get('wiki_url', 'N/A')}")
        else:
            print(f"❌ FAILED to find item with ID {item_id}")

if __name__ == "__main__":
    test_lookup() 