import requests
import re
import json
import os
import random
from bs4 import BeautifulSoup

# Cache file to avoid repeated scraping
CACHE_FILE = "collection_log_data.json"

def scrape_collection_log():
    """Scrape collection log data from the OSRS Wiki"""
    # Check if cache file exists
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            data = json.load(f)
            print(f"Loaded cached data with {len(data['items'])} items and {len(data['unique_items'])} unique items")
            return data
    
    print("Scraping collection log data from the OSRS Wiki...")
    
    # Get the HTML content of the collection log page
    url = "https://oldschool.runescape.wiki/w/Collection_log"
    headers = {
        "User-Agent": "OSRS-Collection-Log-Randomizer/1.0 (Collection log research)"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    # Parse with BeautifulSoup to extract structure
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Initialize data structure
    collection_log = {}
    all_items = []
    
    # Find all h2 elements (main categories)
    h2_elements = soup.find_all('h2')
    
    # Process each main category
    for h2 in h2_elements:
        headline = h2.find('span', class_='mw-headline')
        if not headline:
            continue
        
        category_name = headline.text.strip()
        
        # Skip navigation elements and other non-collection log parts
        if category_name in ['Contents', 'Navigation menu', 'Combat stats', 'Ranks', 'Notes and references']:
            continue
        
        print(f"Processing category: {category_name}")
        collection_log[category_name] = {}
        
        # Find the next h2 (to limit our search area)
        next_h2 = h2.find_next('h2')
        
        # Find all h3 elements between current h2 and next h2
        current_element = h2.next_sibling
        current_subcategory = None
        
        while current_element and current_element != next_h2:
            # Check if this is an h3 (subcategory)
            if getattr(current_element, 'name', None) == 'h3':
                headline = current_element.find('span', class_='mw-headline')
                if headline:
                    current_subcategory = headline.text.strip()
                    print(f"  Processing subcategory: {current_subcategory}")
                    collection_log[category_name][current_subcategory] = []
            
            # If this is a table and we have a subcategory, extract items
            elif getattr(current_element, 'name', None) == 'table' and current_subcategory:
                # Get all table cells - each cell typically contains one item
                for td in current_element.select('td'):
                    # In the collection log, each item appears as both an image link and a text link
                    # To avoid counting twice, we'll only take the text link (which is usually the last link in the cell)
                    links = td.find_all('a', href=True, title=True)
                    
                    # Skip empty cells or cells with no valid links
                    if not links:
                        continue
                    
                    # Find the main link for this item (typically the last non-image link in the cell)
                    main_link = None
                    for link in links:
                        href = link.get('href', '')
                        title = link.get('title', '')
                        
                        # Skip image links and other non-item links
                        if (not href.startswith('/w/')) or ':' in title or href.startswith('/w/File:'):
                            continue
                        
                        # If this link has no img tag as direct child, it's likely the text link
                        if not link.find('img', recursive=False):
                            main_link = link
                    
                    # If we found a main link, process it
                    if main_link:
                        # Get item details
                        href = main_link.get('href', '')
                        title = main_link.get('title', '')
                        
                        # Find the image (could be in another link)
                        img_url = ""
                        img_tag = td.select_one('img')
                        if img_tag and img_tag.get('src'):
                            img_url = f"https://oldschool.runescape.wiki{img_tag.get('src')}"
                        
                        # Create item object
                        item = {
                            "name": title,
                            "url": f"https://oldschool.runescape.wiki{href}",
                            "icon": img_url,
                            "category": category_name,
                            "subcategory": current_subcategory
                        }
                        
                        # Add to collection log
                        collection_log[category_name][current_subcategory].append(item)
                        all_items.append(item)
            
            # Move to the next element
            current_element = current_element.next_sibling
    
    # Get unique items
    unique_items = {}
    for item in all_items:
        name = item["name"]
        if name not in unique_items:
            unique_items[name] = item.copy()
            unique_items[name]["sources"] = []
        
        # Add source information
        unique_items[name]["sources"].append({
            "category": item["category"],
            "subcategory": item["subcategory"]
        })
    
    # Print stats
    print(f"Total items found: {len(all_items)}")
    print(f"Unique items found: {len(unique_items)}")
    print(f"According to the wiki, there are 1,766 slots with 1,568 unique entries")
    
    # Find most duplicated items
    item_counts = {}
    for item in all_items:
        name = item["name"]
        if name in item_counts:
            item_counts[name] += 1
        else:
            item_counts[name] = 1
    
    duplicate_items = {name: count for name, count in item_counts.items() if count > 1}
    top_duplicates = sorted(duplicate_items.items(), key=lambda x: x[1], reverse=True)[:10]
    
    print("\nTop items that appear multiple times:")
    for name, count in top_duplicates:
        print(f"- {name}: {count} occurrences")
    
    # Save to cache file
    cache_data = {
        "structure": collection_log,
        "items": all_items,
        "unique_items": list(unique_items.values())
    }
    
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache_data, f, indent=2)
    
    return cache_data

def get_random_collection_log_item(include_duplicates=False):
    """Get a random item from the collection log
    
    Args:
        include_duplicates: If True, includes all item instances (e.g., Dragon pickaxe from all bosses),
                           which means items in multiple places have higher chance.
                           If False (default), gives equal chance to all unique items.
    """
    data = scrape_collection_log()
    
    if include_duplicates:
        # Choose from all item instances
        # Note: This gives items that appear in multiple places a higher chance
        if data["items"]:
            return random.choice(data["items"])
        return None
    else:
        # Choose from unique items only (equal probability)
        if data["unique_items"]:
            return random.choice(data["unique_items"])
        return None

if __name__ == "__main__":
    # Get a random item from the unique items list (default, equal probability)
    unique_item = get_random_collection_log_item()
    print(f"\nRandom item (equal probability): {unique_item['name']}")
    
    # Show all sources for this item
    print(f"Sources for {unique_item['name']}:")
    for source in unique_item["sources"]:
        print(f"- {source['category']} > {source['subcategory']}")
    
    # Optionally, demonstrate the weighted probability mode
    print("\n--- Optional: Weighted Probability Mode ---")
    print("In this mode, items that appear in multiple places have a higher chance of being selected")
    item = get_random_collection_log_item(include_duplicates=True)
    print(f"Random item (weighted by occurrences): {item['name']} from {item['category']} - {item['subcategory']}") 