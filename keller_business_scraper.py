import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import re
import os

class BusinessScraper:
    def __init__(self):
        self.driver = None
        self.results = []
        self.location = "Keller, TX"
        self.target_count = 5
        self.found_count = 0
        self.found_businesses = set()  # Keep track of businesses we've found

    def setup_driver(self):
        """Initialize the Chrome WebDriver"""
        options = webdriver.ChromeOptions()
        # Basic options for stability
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-notifications')
        # Suppress console logging
        options.add_argument('--log-level=3')  # Fatal only
        options.add_argument('--silent')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        print("Browser started successfully")

    def highlight_element(self, element, color="yellow"):
        """Highlight an element on the page"""
        self.driver.execute_script(
            "arguments[0].style.backgroundColor = '#ffeb3b';"  # Bright yellow
            "arguments[0].style.border = '4px solid #f44336';"  # Red border
            "arguments[0].style.padding = '10px';"
            "arguments[0].style.boxShadow = '0 0 10px rgba(0,0,0,0.5)';"  # Add shadow
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",  # Scroll into view
            element)
        time.sleep(1)  # Keep highlight visible for a moment

    def search_businesses(self):
        """Search for businesses in Keller, TX using Google Maps"""
        try:
            print("Navigating to Google Maps...")
            self.driver.get("https://www.google.com/maps")
            time.sleep(3)

            print(f"Searching for businesses in {self.location}...")
            try:
                # Find and click the searchbox
                search_box = self.driver.find_element(By.ID, "searchboxinput")
                search_box.click()
                time.sleep(1)
                
                # Enter search
                search_box.clear()
                search_query = "mechanics near me"
                search_box.send_keys(search_query)
                search_box.send_keys(Keys.RETURN)
                print(f"Search query submitted: '{search_query}'")
                print(f"\nSearching for {self.target_count} unique businesses without websites...")
                print("(This may take a few minutes as we check each business)\n")
                time.sleep(7)

                # Process results
                last_height = 0
                no_new_results_count = 0
                processed_businesses = set()  # Track all businesses we've seen
                scroll_attempts = 0
                max_scroll_attempts = 30  # Maximum number of scroll attempts

                print("\nScrolling through results to find businesses...")
                while self.found_count < self.target_count and scroll_attempts < max_scroll_attempts:
                    try:
                        # Find all business elements in the sidebar
                        business_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div.Nv2PK')
                        
                        if business_elements:
                            found_new_business = False
                            for element in business_elements:
                                if self.found_count >= self.target_count:
                                    break
                                    
                                try:
                                    # Get business name
                                    name_element = element.find_element(By.CSS_SELECTOR, 'div.qBF1Pd')
                                    name = name_element.text.strip()
                                    
                                    # Skip if we've already processed this business
                                    if not name or name in processed_businesses:
                                        continue
                                        
                                    # Add to processed set immediately
                                    processed_businesses.add(name)
                                    print(f"\nChecking business: {name} ({len(processed_businesses)} total checked)")
                                    
                                    # Look for Website link using the specific classes
                                    try:
                                        website_element = element.find_element(By.CSS_SELECTOR, 'a.lcr4fd.S9kvJb')
                                        # If we found the website element, skip this business
                                        print(f"Skipping {name} - Has website")
                                        continue
                                    except NoSuchElementException:
                                        # No website found - click to check reviews
                                        try:
                                            # Click the business to open details
                                            clickable = element.find_element(By.CSS_SELECTOR, 'a.hfpxzc')
                                            self.driver.execute_script("arguments[0].click();", clickable)
                                            time.sleep(3)  # Wait for details to load
                                            
                                            try:
                                                # Find and click the Reviews tab
                                                reviews_tab = self.driver.find_element(By.CSS_SELECTOR, 'button[aria-label*="Reviews"]')
                                                self.driver.execute_script("arguments[0].click();", reviews_tab)
                                                time.sleep(2)
                                                
                                                # Get rating
                                                rating_element = self.driver.find_element(By.CSS_SELECTOR, 'div.fontDisplayLarge')
                                                rating = float(rating_element.text.strip())
                                                
                                                # Get all review dates
                                                review_dates = self.driver.find_elements(By.CSS_SELECTOR, 'span.rsqaWe')
                                                has_recent_review = False
                                                latest_review_text = "No reviews found"
                                                
                                                # Check for recent reviews (3 years or less)
                                                for date_element in review_dates:
                                                    review_date = date_element.text.strip().lower()
                                                    print(f"Found review date: {review_date}")
                                                    
                                                    # If date contains 'year' or 'years'
                                                    if 'year' in review_date:
                                                        match = re.search(r'(\d+)', review_date)
                                                        if match:
                                                            years = int(match.group(1))
                                                            if years <= 3:  # Changed to <= 3 to include reviews from last 3 years
                                                                has_recent_review = True
                                                                latest_review_text = review_date
                                                                print(f"Found recent review: {years} years ago")
                                                                break
                                                    # If date contains any of these, it's definitely recent
                                                    elif any(word in review_date for word in ['month', 'week', 'day', 'hour', 'minute', 'second']):
                                                        has_recent_review = True
                                                        latest_review_text = review_date
                                                        print(f"Found recent review: {review_date}")
                                                        break
                                                
                                                print(f"Found rating: {rating} ⭐")
                                                if has_recent_review:
                                                    print(f"Found recent review: {latest_review_text}")
                                                else:
                                                    print("No recent reviews found - skipping")
                                                
                                                # Check if meets all criteria (now including recent reviews)
                                                if rating >= 3.0 and has_recent_review:  # Changed to require recent reviews
                                                    self.found_count += 1
                                                    self.found_businesses.add(name)
                                                    found_new_business = True
                                                    print("\n" + "="*50)
                                                    print(f"✅ POTENTIAL LEAD FOUND! ({self.found_count}/{self.target_count})")
                                                    print(f"Business Name: {name}")
                                                    print(f"Rating: {rating} ⭐")
                                                    print(f"Most Recent Review: {latest_review_text}")
                                                    print("Status: No website, rating ≥ 3.0, has recent reviews")
                                                    print("="*50)
                                                    self.highlight_element(element)
                                                    input("📝 Take note of this business and press Enter to continue...\n")
                                                else:
                                                    if rating < 3.0:
                                                        print(f"Skipping {name} - Rating too low ({rating})")
                                                    elif not has_recent_review:
                                                        print(f"Skipping {name} - No recent reviews")
                                            except Exception as e:
                                                print(f"Error checking reviews tab for {name}: {str(e)}")
                                                continue
                                                
                                        except Exception as e:
                                            print(f"Error checking reviews for {name}: {str(e)}")
                                            continue
                                except Exception as e:
                                    print(f"Error processing business: {str(e)}")
                                    continue
                        
                        # Scroll the feed if we haven't found enough businesses
                        if self.found_count < self.target_count:
                            try:
                                feed = self.driver.find_element(By.CSS_SELECTOR, 'div.m6QErb')
                                
                                # Get current scroll height
                                new_height = self.driver.execute_script('return arguments[0].scrollTop', feed)
                                
                                # If we haven't found any new businesses and haven't scrolled further
                                if not found_new_business and new_height == last_height:
                                    no_new_results_count += 1
                                    print(f"\nTrying to find more results... (Attempt {no_new_results_count}/5)")
                                    # Try scrolling a bit more aggressively
                                    self.driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight + 1000', feed)
                                else:
                                    no_new_results_count = 0  # Reset counter if we found new businesses or scrolled further
                                
                                last_height = new_height
                                scroll_attempts += 1
                                
                                # Scroll down
                                self.driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', feed)
                                print(f"\nScrolling for more businesses... (Scroll {scroll_attempts}/{max_scroll_attempts})")
                                time.sleep(3)  # Wait for new results to load
                            except Exception as e:
                                print(f"Error scrolling: {str(e)}")
                                no_new_results_count += 1
                                
                    except Exception as e:
                        print(f"Error in scroll iteration: {str(e)}")
                        scroll_attempts += 1
                        continue

                if self.found_count >= self.target_count:
                    print(f"\nSuccess! Found {self.found_count} businesses matching all criteria!")
                    print(f"Checked a total of {len(processed_businesses)} businesses")
                else:
                    print(f"\nOnly found {self.found_count} matching businesses after checking {len(processed_businesses)} total.")
                    print("Try modifying the search query or checking a different area.")

            except Exception as e:
                print(f"Error during search: {e}")

        except Exception as e:
            print(f"Error in search_businesses: {e}")

    def run(self):
        """Main execution method"""
        try:
            print("Starting business search...")
            self.setup_driver()
            self.search_businesses()
            input("\nSearch complete. Press Enter to close the browser...")
        except Exception as e:
            print(f"Critical error: {e}")
        finally:
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    scraper = BusinessScraper()
    scraper.run() 