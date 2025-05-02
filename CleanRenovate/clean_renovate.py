from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv

class Nexus:
    """
    Class for interacting with the Nexus repository
    """
    def __init__(self, headless=False):
        """
        Initialize the Nexus class with a Playwright browser
        """
        # Load environment variables from .env file
        load_dotenv()
        self.base_url = os.getenv("BASE_URL")
        if not self.base_url:
            raise ValueError("BASE_URL not found in .env file")
        # Ensure base_url ends with a slash
        if not self.base_url.endswith('/'):
            self.base_url += '/'
            
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless)
        self.page = self.browser.new_page()
        self.page.set_default_timeout(10000)  # Set global timeout to 10 seconds (10000ms)
        self.is_logged_in = False

    def login(self):
        """
        Login to the Nexus repository using credentials from .env file
        """
        if self.is_logged_in:
            return
            
        # Load environment variables from .env file
        username = os.getenv("USERNAME")
        password = os.getenv("PASSWORD")
        
        if not username or not password:
            raise ValueError("Username or password not found in .env file")
        
        # Navigate to login page using base_url
        login_url = self.base_url
        self.page.goto(login_url)
        
        # Fill in login form
        self.page.click('#nx-header-signin-1149-btnEl')
        self.page.fill('#textfield-1281-inputEl', username)
        self.page.fill('#textfield-1282-inputEl', password)
        
        # Submit form
        self.page.click('#button-1284')
        
        self.is_logged_in = True
        print("Login successful")
    
    def extract_tags(self, fetch_tags, excluded_tags=[]):
        """
        Extract tags from the specified Nexus repository
        
        Returns:
            List of tag names (excluding 'latest' and 'Parent Directory')
        """
        # Make sure we're logged in
        if not self.is_logged_in:
            self.login()
        
        tags = []

        for fetch_tag in fetch_tags:
            # Navigate to the tags page using base_url
            tags_url = f"{self.base_url}service/rest/repository/browse/docker-hosted/v2/kwm/{fetch_tag}/tags"
            self.page.goto(tags_url)
            
            # Wait for the table to load
            self.page.wait_for_selector('table')
            
            # Extract tag names from the anchor elements inside first table cell
            
            tag_elements = self.page.query_selector_all('table tr td:first-child a')
            for element in tag_elements:
                tag_text = element.inner_text()
                if tag_text and tag_text.strip() and tag_text.strip() not in excluded_tags:
                    tags.append(tag_text.strip())
            
        return tags
    
    def remove_tag(self, tag):
        """
        Remove a specific tag from the repository
        
        Args:
            tag: Tag to remove
            
        Returns:
            Boolean indicating if the tag was successfully removed
        """
        # Make sure we're logged in
        if not self.is_logged_in:
            self.login()
            
        # Navigate to search URL with the tag using base_url
        search_url = f"{self.base_url}#browse/search=attributes.docker.imageTag%3D{tag}"
        self.page.goto(search_url)
        
        # Wait for the page and search results to load
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_selector('div.x-grid-item-container', timeout=10000)

        # Fill in the search text and hit Enter to confirm
        self.page.fill('#nx-coreui-searchcriteria-text-1233-inputEl', tag)
        self.page.press('#nx-coreui-searchcriteria-text-1233-inputEl', 'Enter')

        # Check if search results contain any items and get count
        items = self.page.query_selector_all('//tbody/tr/td[2]/div[contains(.,"kwm")]')
        
        if not items:
            print(f"Tag {tag} not found in search results.")
            return False
            
        print(f"Found {len(items)} items for tag '{tag}', attempting to remove...")
        
        for _ in items:
            try:
                # Get the item name for verification later
                self.page.wait_for_load_state("domcontentloaded")
                self.page.wait_for_selector('(//tbody/tr/td[2]/div[contains(.,"kwm")])[1]', state='visible', timeout=10000)
                item = self.page.query_selector('(//tbody/tr/td[2]/div[contains(.,"kwm")])[1]')
                item_name = item.inner_text().strip()
                
                print(f"Removing item: {item_name}")
                
                # Click on the item to select it using page.click instead of ElementHandle.click
                self.page.wait_for_timeout(1000)  # Wait for the item to be clickable
            
                self.page.click('(//tbody/tr/td[2]/div[contains(.,"kwm")])[1]')
                self.page.click('#nx-button-1209-btnInnerEl')
                self.page.click('#button-1006-btnEl')

                # Wait for the confirmation dialog to appear
                self.page.wait_for_load_state("domcontentloaded")
                self.page.wait_for_selector(f'//tbody/tr/td[2]/div[contains(.,"{item_name}")]', 
                                          state="hidden", 
                                          timeout=10000)
                self.page.wait_for_timeout(1500)
                print(f"Successfully removed: {item_name}")
            except Exception as e:
                print(f"Failed to verify removal of {item_name}: {str(e)}")

    def close(self):
        """
        Close the browser and clean up resources
        """
        if self.browser:
            self.browser.close()
            self.browser = None
        if self.playwright:
            self.playwright.stop()
            self.playwright = None


if __name__ == "__main__":
    # Create a Nexus instance
    nexus = Nexus(headless=False)
    
    try:
        # Login
        nexus.login()
        
        # Extract tags
        tags = nexus.extract_tags(["db", "kwm-importer", "kwm-keycloak", "kwm-ldap", "kwm-portal", "pom-mock"], excluded_tags=["latest", "Parent Directory"])
        
        print(f"Found {len(tags)} tags:")
        for tag in tags:
            print(f"- {tag}")
        
        # Process each tag
        for tag in tags:
            # Search and remove the tag
            nexus.remove_tag(tag)
    
    finally:
        # Make sure we clean up resources
        nexus.close()
