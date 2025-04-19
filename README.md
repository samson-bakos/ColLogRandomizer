# OSRS Collection Log Randomizer

A tool that randomly generates an item from Old School RuneScape's collection log. It scrapes data directly from the [OSRS Wiki](https://oldschool.runescape.wiki/w/Collection_log) to stay up to date with changes to the log.

## Features

- Generate a random item from the OSRS collection log
- Displays the item name, source, category, and icon
- Shows all locations where an item can be obtained if it appears in multiple places
- **Temple Mode**: Filter out items you've already collected (requires OSRS username)
- Data is sourced directly from the OSRS Wiki and TempleOSRS API
- Clean, simple interface

## Screenshots

![OSRS Collection Log Randomizer](https://i.imgur.com/example.png) *(Replace with an actual screenshot)*

## Setup and Installation

1. Clone this repository:
```
git clone https://github.com/yourusername/osrs-collection-log-randomizer.git
cd osrs-collection-log-randomizer
```

2. Install the required dependencies:
```
pip install -r requirements.txt
```

3. Run the application:
```
streamlit run app.py
```

4. The application will open in your default web browser. If it doesn't, navigate to `http://localhost:8501`.

## How It Works

### Regular Mode
1. The application scrapes collection log data from the OSRS Wiki.
2. Data is cached locally to avoid repeated scraping.
3. When you click "Roll for Random Collection Log Item," a random item is selected from the database.
4. The item's name, source, category, and icon are displayed.
5. If the item appears in multiple places in the collection log, all sources are shown.

### Temple Mode
1. Enter your OSRS username (RSN)
2. The app fetches your collection log data from the TempleOSRS API
3. It filters out items you've already collected
4. Rolls randomly from the items you still need to collect
5. Perfect for generating random collection log tasks to work towards

## Files

- `app.py` - The Streamlit web interface
- `collection_log_randomizer.py` - Backend logic for scraping data and selecting random items
- `temple_api.py` - Handles interactions with the TempleOSRS API
- `collection_log_data.json` - Cached collection log data (created on first run)
- `cache/` - Directory for storing cached player data from TempleOSRS

## Implementation Details

The collection log contains around 1,766 total slots with 1,568 unique items. Some items appear in multiple places (like Dragon pickaxe which can be obtained from several bosses). Our randomizer gives each unique item an equal chance of being selected.

In Temple Mode, the app uses the TempleOSRS API to fetch your personal collection log progress, then filters the random selection to only show items you haven't yet collected. This makes it perfect for generating random collection log tasks to work towards.

## Credits

- Data sourced from the [Old School RuneScape Wiki](https://oldschool.runescape.wiki/)
- Player collection data from [TempleOSRS](https://templeosrs.com/)
- Icons and item information © Jagex Ltd.

## License

This project is for educational purposes only. All Old School RuneScape content and materials are the intellectual property of Jagex Ltd. 