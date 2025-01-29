# Keller Business Scraper

This application scrapes information about businesses in Keller, TX that meet the following criteria:
- Have a rating of 4.0 or above on Google Reviews
- Don't have a website listed on Google
- Have a Facebook page

## Setup

1. Install Python 3.8 or higher if you haven't already
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory and add your Google Places API key:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

   To get a Google Places API key:
   1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
   2. Create a new project or select an existing one
   3. Enable the Places API
   4. Create credentials (API key)
   5. Copy the API key to your `.env` file

## Usage

Run the scraper:
```
python keller_business_scraper.py
```

The results will be saved to `keller_businesses.csv` with the following information:
- Business name
- Address
- Phone number
- Rating

## Requirements
- Python 3.8+
- Chrome browser installed
- Internet connection
- Google Places API key 