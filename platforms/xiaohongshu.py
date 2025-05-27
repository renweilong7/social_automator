# platforms/xiaohongshu.py
# 继承 BasePlatform，使用 Playwright 实现小红书平台的具体逻辑。

from typing import List, Optional, Dict, Any
from playwright.sync_api import sync_playwright, Page, BrowserContext, Playwright

from base_platform import BasePlatform, PostData, CommentData, PostDetailData
from accounts.models import Account
from accounts.playwright_auth import PlaywrightAuthManager
# Assuming settings are available for Playwright configurations
from config.settings import settings
# Assuming utility functions for Playwright might be helpful
# from ..utils.playwright_utils import safe_click, scroll_page

class XiaohongshuPlatform(BasePlatform):
    """
    Xiaohongshu (Little Red Book) platform implementation using Playwright.
    """
    BASE_URL = "https://www.xiaohongshu.com"

    def __init__(self, playwright_instance: Optional[Playwright] = None):
        super().__init__(platform_name="Xiaohongshu")
        self.playwright = playwright_instance or sync_playwright().start()
        self.browser: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.auth_manager = PlaywrightAuthManager(cookies_dir=settings.COOKIES_DIR)
        self._logged_in_account: Optional[Account] = None

    def _ensure_browser_page(self, new_context_for_login: bool = False) -> Page:
        """Ensures browser and page are initialized."""
        if new_context_for_login or self.browser is None or self.page is None or self.page.is_closed():
            if self.browser and not new_context_for_login: # If page is closed but browser exists
                try:
                    self.page = self.browser.new_page()
                    print("New page created in existing browser context.")
                    return self.page
                except Exception as e:
                    print(f"Failed to create new page in existing context: {e}. Re-launching browser.")
            
            # Close existing browser if any before creating a new one
            if self.browser:
                try: self.browser.close() 
                except: pass

            browser_instance = self.playwright.chromium.launch(
                headless=settings.PLAYWRIGHT_HEADLESS,
                slow_mo=settings.PLAYWRIGHT_SLOW_MO
            )
            self.browser = browser_instance.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                # viewport={'width': 1280, 'height': 720} # Optional: set viewport
            )
            self.browser.set_default_timeout(settings.PLAYWRIGHT_TIMEOUT)
            self.page = self.browser.new_page()
            print("New browser context and page initialized for Xiaohongshu.")
        return self.page

    def login(self, account: Account) -> bool:
        """
        Logs into Xiaohongshu. Tries to load cookies first, then attempts QR code scan.
        """
        self._ensure_browser_page(new_context_for_login=True) # Use a fresh context for login attempts
        page = self.page
        assert page is not None, "Page should be initialized"
        assert self.browser is not None, "Browser context should be initialized"

        if account.cookies_file and self.auth_manager.load_cookies(self.browser, account.cookies_file):
            print(f"Successfully loaded cookies for {account.username} from {account.cookies_file}")
            # Verify login by visiting a protected page or checking for user-specific elements
            page.goto(f"{self.BASE_URL}/explore", wait_until="networkidle") # Go to a common page
            # Add a check here to confirm login status, e.g., looking for a profile icon
            # For now, assume cookie load means logged in if verification is complex
            # Example check (highly dependent on XHS UI):
            # if page.query_selector("//div[contains(@class, 'avatar-container')]//img[@alt='avatar']"): # Placeholder selector
            #     print("Login verified via cookies.")
            #     self._logged_in_account = account
            #     return True
            # else:
            #     print("Cookie loaded, but login verification failed. Proceeding to manual login.")
            print("Login assumed successful after loading cookies (add verification step for robustness).")
            self._logged_in_account = account
            return True # Assuming for now, needs robust verification

        print(f"Cookies for {account.username} not found or failed to load. Attempting manual login (QR Scan)...")
        page.goto(f"{self.BASE_URL}/login", wait_until="domcontentloaded")
        
        # Xiaohongshu login is typically QR code based on web
        print("Please scan the QR code on the Xiaohongshu login page in the browser within 60 seconds.")
        try:
            # Wait for user to scan QR code and for navigation to a logged-in page (e.g., explore or home)
            # This is a simplified wait; a more robust solution would check for specific elements indicating login success.
            page.wait_for_url(lambda url: "/explore" in url or "/home" in url or "/me/profile" in url, timeout=60000) # 60s for QR scan
            print("Login successful (detected navigation to a logged-in area).")
            
            if account.cookies_file:
                self.auth_manager.save_cookies(self.browser, account.cookies_file)
            else:
                # Generate a cookie file name if not provided
                generated_cookie_file = f"{account.username}_{self.platform_name.lower()}_cookies.json"
                print(f"Account.cookies_file not set, will attempt to save to: {generated_cookie_file}")
                self.auth_manager.save_cookies(self.browser, generated_cookie_file)
                # It's good practice to update the account object in your account manager if a new cookie file is created.

            self._logged_in_account = account
            return True
        except Exception as e:
            print(f"Login failed or timed out: {e}")
            return False

    def search_posts(self, keywords: List[str], count: int = 10) -> List[PostData]:
        if not self._logged_in_account:
            print("Not logged in. Please login first.")
            return []
        page = self._ensure_browser_page()
        query = " ".join(keywords)
        search_url = f"{self.BASE_URL}/search_result?keyword={query}&source=unknown"
        print(f"Searching Xiaohongshu for: '{query}'")
        page.goto(search_url, wait_until="networkidle")
        
        # Placeholder: Actual selectors for Xiaohongshu search results are needed here.
        # This will require inspecting the XHS website structure.
        # Example (pseudo-code, selectors will be different):
        # posts_elements = page.query_selector_all("div.note-item") # This is a guess
        # results = []
        # for i, el in enumerate(posts_elements):
        #     if len(results) >= count: break
        #     try:
        #         post_id = el.get_attribute('data-id') # Guess
        #         post_url = el.query_selector('a.cover').get_attribute('href') # Guess
        #         title = el.query_selector('div.title').inner_text() # Guess
        #         author = el.query_selector('div.author').inner_text() # Guess
        #         results.append(PostData(id=post_id, url=f"{self.BASE_URL}{post_url}", title=title, author=author))
        #     except Exception as e:
        #         print(f"Error parsing post item {i}: {e}")
        # return results
        print("search_posts: Xiaohongshu selectors need to be implemented.")
        return []

    def extract_post_details(self, post_url: str) -> Optional[PostDetailData]:
        if not self._logged_in_account:
            print("Not logged in. Please login first.")
            return None
        page = self._ensure_browser_page()
        print(f"Extracting details for Xiaohongshu post: {post_url}")
        page.goto(post_url, wait_until="networkidle")
        # Placeholder: Actual selectors for post details needed.
        print("extract_post_details: Xiaohongshu selectors need to be implemented.")
        return None

    def extract_comments(self, post_url: str, count: int = 20) -> List[CommentData]:
        if not self._logged_in_account:
            print("Not logged in. Please login first.")
            return []
        page = self._ensure_browser_page()
        print(f"Extracting comments for Xiaohongshu post: {post_url}")
        if not page.url.startswith(post_url):
             page.goto(post_url, wait_until="networkidle")
        # Placeholder: Actual selectors for comments and logic for scrolling/pagination needed.
        print("extract_comments: Xiaohongshu selectors and pagination logic need to be implemented.")
        return []

    def publish_comment(self, post_url: str, comment_text: str, account: Account) -> bool:
        if not self._logged_in_account or self._logged_in_account.username != account.username:
            print(f"Account {account.username} is not logged in. Current: {self._logged_in_account.username if self._logged_in_account else 'None'}. Please login with the correct account.")
            # Or attempt login with `account`
            # if not self.login(account): return False
            return False
        
        page = self._ensure_browser_page()
        print(f"Publishing comment on Xiaohongshu post: {post_url}")
        if not page.url.startswith(post_url):
            page.goto(post_url, wait_until="networkidle")
        
        # Placeholder: Actual selectors for comment input box and submit button needed.
        # Example (pseudo-code):
        # try:
        #     comment_box = page.wait_for_selector("textarea.comment-input-textarea", timeout=10000) # Guess
        #     await comment_box.fill(comment_text)
        #     await page.wait_for_timeout(500) # Brief pause
        #     submit_button = page.query_selector("button.comment-submit-button") # Guess
        #     await submit_button.click()
        #     await page.wait_for_timeout(3000) # Wait for comment to appear (or for confirmation)
        #     # Add verification that comment was posted
        #     print("Comment published successfully (simulated).")
        #     return True
        # except Exception as e:
        #     print(f"Error publishing comment: {e}")
        #     return False
        print("publish_comment: Xiaohongshu selectors need to be implemented.")
        return False

    def publish_post(self, post_content: Dict[str, Any], account: Account) -> bool:
        if not self._logged_in_account or self._logged_in_account.username != account.username:
            print(f"Account {account.username} is not logged in. Please login with the correct account.")
            return False

        page = self._ensure_browser_page()
        print(f"Attempting to publish post on Xiaohongshu as {account.username}")
        
        # Navigate to the create post page (URL might change)
        create_post_url = f"{self.BASE_URL}/creator/publish/upload"
        page.goto(create_post_url, wait_until="networkidle")
        
        # Placeholder: Logic for filling title, content, uploading images/videos, adding tags.
        # This is highly complex and specific to XHS UI.
        # Example (pseudo-code):
        # text_content = post_content.get('text', '')
        # images = post_content.get('images', []) # List of local file paths
        # 
        # await page.fill("input[name='title']", post_content.get('title', 'My New Post')) # Guess
        # await page.fill("textarea.content-editor", text_content) # Guess
        # 
        # if images:
        #     # Handle file uploads (XHS might use a file input or drag-drop)
        #     # file_input = await page.query_selector("input[type='file'].uploader") # Guess
        #     # await file_input.set_input_files(images)
        #     pass
        # 
        # await page.click("button.publish-button") # Guess
        # # Add verification of successful post
        print("publish_post: Xiaohongshu post creation flow needs to be implemented.")
        return False

    def close(self):
        if self.browser:
            try:
                self.browser.close()
                print("Xiaohongshu browser context closed.")
            except Exception as e:
                print(f"Error closing Xiaohongshu browser: {e}")
            self.browser = None
            self.page = None
        if self.playwright:
            try:
                # Only stop playwright if this instance started it.
                # If playwright was passed in, the caller is responsible for stopping it.
                # This logic needs refinement based on how playwright_instance is managed.
                # For now, assume if self.playwright exists, this class might have started it.
                # A better approach is a flag: self._started_playwright = True if self.playwright.start() was called by this class.
                # sync_playwright().stop() # This would stop the global instance, be careful.
                # If playwright was started by this instance:
                # self.playwright.stop() # This is not a method on the Playwright object from sync_playwright().start()
                # The .start() returns a Playwright object, which doesn't have a .stop() method itself.
                # The context manager `with sync_playwright() as p:` handles cleanup.
                # If started manually, it's often not explicitly stopped until script end or if part of a larger manager.
                pass # Playwright cleanup is tricky when not using 'with' statement.
            except Exception as e:
                print(f"Error stopping Playwright for Xiaohongshu: {e}")
        self._logged_in_account = None
        print("Xiaohongshu platform resources released.")

if __name__ == '__main__':
    print("Testing XiaohongshuPlatform...")
    # This test requires manual interaction for QR code login if cookies are not present.
    # Ensure you have a .env file or settings configured for paths.
    # Create a dummy account for testing
    test_account_details = {
        "username": "test_xhs_user", 
        "platform": "Xiaohongshu", 
        "password": "dummy_password", # Not used for QR login
        "cookies_file": "test_xhs_user_xiaohongshu_cookies.json" # Will be created if login is successful
    }
    test_account = Account(**test_account_details)

    # Ensure data/cookies directory exists (settings should handle this, but double check for standalone test)
    settings.COOKIES_DIR.mkdir(parents=True, exist_ok=True)

    xhs_platform = None
    try:
        with sync_playwright() as p_instance:
            xhs_platform = XiaohongshuPlatform(playwright_instance=p_instance)
            print(f"Attempting to login with account: {test_account.username}")
            login_success = xhs_platform.login(test_account)

            if login_success:
                print(f"Login successful for {test_account.username}.")
                
                # --- Test Search (will print 'not implemented') ---
                # print("\nTesting post search...")
                # posts = xhs_platform.search_posts(keywords=["美食"], count=2)
                # if posts:
                #     for post in posts:
                #         print(f"  Found post: {post.title} ({post.url})")
                # else:
                #     print("  No posts found or search not fully implemented.")

                # --- Test Post Detail Extraction (will print 'not implemented') ---
                # Example post URL (replace with a real one if testing manually)
                # test_post_url = "https://www.xiaohongshu.com/explore/some_post_id"
                # print(f"\nTesting post detail extraction for: {test_post_url}")
                # details = xhs_platform.extract_post_details(test_post_url)
                # if details:
                #     print(f"  Post Title: {details.title}")
                #     print(f"  Full Content Snippet: {details.full_content[:100]}...")
                # else:
                #     print("  Could not extract post details or not implemented.")

                # --- Test Comment Publishing (will print 'not implemented') ---
                # print("\nTesting comment publishing...")
                # comment_published = xhs_platform.publish_comment(
                #     post_url=test_post_url, 
                #     comment_text="这是一个测试评论！", 
                #     account=test_account
                # )
                # print(f"  Comment publish status: {comment_published}")

            else:
                print(f"Login failed for {test_account.username}. Further tests will be skipped.")
                print("If this was a QR login, ensure you scanned it. If cookies, they might be invalid.")

    except Exception as e:
        print(f"An error occurred during XiaohongshuPlatform test: {e}")
    finally:
        if xhs_platform:
            xhs_platform.close()
        print("XiaohongshuPlatform test finished.")