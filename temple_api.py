"""
Temple OSRS API module for fetching player collection log data
"""
import requests
import json
import time
import os
from typing import Dict, List, Optional, Union, Any

# Cache directory
CACHE_DIR = "cache"
# Time to keep cache (24 hours in seconds)
CACHE_TTL = 24 * 60 * 60

class TempleApi:
    """TempleOSRS API handler"""
    
    def __init__(self, cache_dir: str = CACHE_DIR):
        """Initialize the Temple API handler"""
        self.cache_dir = cache_dir
        # Create cache directory if it doesn't exist
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def _get_cache_path(self, rsn: str) -> str:
        """Get the path to the cache file for a player"""
        # Clean the RSN to create a valid filename
        clean_rsn = "".join(c if c.isalnum() else "_" for c in rsn)
        return os.path.join(self.cache_dir, f"{clean_rsn}.json")
    
    def _is_cache_valid(self, cache_path: str) -> bool:
        """Check if a cache file is still valid"""
        if not os.path.exists(cache_path):
            return False
        
        # Check if the file is older than the TTL
        modified_time = os.path.getmtime(cache_path)
        current_time = time.time()
        return (current_time - modified_time) < CACHE_TTL
    
    def _read_cache(self, cache_path: str) -> Dict:
        """Read data from the cache"""
        with open(cache_path, 'r') as f:
            return json.load(f)
    
    def _write_cache(self, cache_path: str, data: Dict) -> None:
        """Write data to the cache"""
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_collection_log(self, rsn: str, force_refresh: bool = False) -> Dict:
        """
        Get a player's collection log data from Temple OSRS
        
        Args:
            rsn: The player's RuneScape Name
            force_refresh: If True, ignore cache and fetch fresh data
            
        Returns:
            Dictionary with the player's collection log data
        """
        # Check cache first
        cache_path = self._get_cache_path(rsn)
        if not force_refresh and self._is_cache_valid(cache_path):
            return self._read_cache(cache_path)
        
        # If not in cache or forced refresh, fetch from API
        # Manually replace spaces with %20 to match exactly the format that worked
        encoded_rsn = rsn.replace(" ", "%20")
        
        # Use the working URL format for the Temple API
        url = f"https://templeosrs.com/api/collection-log/player_collections.php?player={encoded_rsn}"
        
        # Use the same headers that worked
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Referer": "https://templeosrs.com/",
            "Accept": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API errors
            if isinstance(data, dict) and "error" in data:
                return {"error": data["error"]}
            
            # Add some stats from the data
            if "data" in data and "items" in data["data"]:
                items = data["data"]["items"]
                total_items = len(items)
                owned_items = sum(1 for _, item_data in items.items() 
                                 if isinstance(item_data, dict) and item_data.get("count", 0) > 0)
                
                # Add these stats to the response
                if "data" not in data:
                    data["data"] = {}
                
                data["data"]["total_collections_available"] = total_items
                data["data"]["total_collections_finished"] = owned_items
            
            # Save valid data to cache
            self._write_cache(cache_path, data)
            return data
                
        except json.JSONDecodeError as e:
            return {"error": f"Error parsing TempleOSRS API response: {str(e)}"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Error connecting to TempleOSRS API: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    def get_unowned_items(self, rsn: str, force_refresh: bool = False) -> List[str]:
        """
        Get a list of unowned item IDs for a player
        
        Args:
            rsn: The player's RuneScape Name
            force_refresh: If True, ignore cache and fetch fresh data
            
        Returns:
            List of unowned item IDs (as strings)
        """
        data = self.get_collection_log(rsn, force_refresh)
        
        if "error" in data:
            return []
        
        unowned_ids = []
        
        # The API response has a simple structure where items is a dictionary
        # with item IDs as keys, and each value has a "count" field
        if "data" in data and "items" in data["data"]:
            items = data["data"]["items"]
            
            # Extract items with count=0 (unowned)
            for item_id, item_data in items.items():
                if isinstance(item_data, dict) and item_data.get("count", 0) == 0:
                    unowned_ids.append(item_id)
        
        return unowned_ids

if __name__ == "__main__":
    # Test the API with the correct endpoint
    temple = TempleApi()
    rsn = "Iron Beeto"
    print(f"Fetching collection log for {rsn}...")
    data = temple.get_collection_log(rsn)
    
    if "error" in data:
        print(f"Error: {data['error']}")
    else:
        print(f"Successfully retrieved collection log data for {rsn}")
        
        # Display collection log stats
        if "data" in data:
            data_obj = data["data"]
            if "total_collections_finished" in data_obj and "total_collections_available" in data_obj:
                finished = data_obj["total_collections_finished"]
                total = data_obj["total_collections_available"]
                print(f"Collection log: {finished}/{total} items")
        
        # Get unowned items
        unowned = temple.get_unowned_items(rsn)
        if unowned:
            print(f"{rsn} doesn't own {len(unowned)} items")
            print(f"First few unowned IDs: {unowned[:5]}")
        else:
            print(f"No unowned items found for {rsn} or couldn't parse the data correctly") 