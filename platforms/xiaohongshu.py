# platforms/xiaohongshu.py
# 继承 BasePlatform，使用 Playwright 实现小红书平台的具体逻辑。

from typing import List, Optional, Dict, Any
from playwright.sync_api import sync_playwright, Page, BrowserContext, Playwright
from pathlib import Path

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

    def _get_user_data_dir(self, account: Account) -> Path:
        """Generates the user data directory path for a given account."""
        # Ensure settings.COOKIES_DIR is a Path object or handle accordingly
        base_data_path = Path(settings.COOKIES_DIR).parent if settings.COOKIES_DIR else Path("data")
        # Sanitize account.username if it can contain characters invalid for directory names
        # For simplicity, using it directly here. Consider account.get_safe_username_for_path()
        safe_username = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in account.username)
        # The user_data_dir is now per account, not per account per platform
        return base_data_path / "browser_user_data" / safe_username

    def _ensure_browser_page(self, for_account: Optional[Account] = None) -> Page:
        """
        Ensures browser context and page are initialized using a persistent context
        for the 'for_account' if provided, otherwise for 'self._logged_in_account'.
        Switches context if 'for_account' is different from current '_logged_in_account'.
        """
        account_to_use = for_account or self._logged_in_account

        if not account_to_use:
            # This situation should ideally be prevented by callers (e.g., login required first)
            # If this happens, it means an operation requiring a browser is called without a user context.
            # For now, raising an error is safer than creating a non-persistent/generic context implicitly.
            raise ValueError("Cannot ensure browser page: No account specified or previously logged in.")

        user_data_dir = self._get_user_data_dir(account_to_use)

        must_launch_new_or_switch_context = False
        if not self.browser :
            must_launch_new_or_switch_context = True
            print("No active browser context or context disconnected. Will launch new.")
        elif self._logged_in_account != account_to_use:  # Switching accounts
            must_launch_new_or_switch_context = True
            print(
                f"Switching persistent context from '{self._logged_in_account.username if self._logged_in_account else 'None'}' to '{account_to_use.username}'.")

        if must_launch_new_or_switch_context:
            if self.browser and self.browser.is_connected():  # Close previous context if exists and connected
                try:
                    print(
                        f"Closing existing browser context for '{self._logged_in_account.username if self._logged_in_account else 'Unknown User'}'.")
                    self.browser.close()
                except Exception as e:
                    print(f"Error closing previous browser context: {e}")

            user_data_dir.mkdir(parents=True, exist_ok=True)
            print(f"Launching/Using persistent context for '{account_to_use.username}' from: {user_data_dir}")
            self.browser = self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(user_data_dir),  # Playwright expects str or Path, str is safer
                headless=settings.PLAYWRIGHT_HEADLESS,
                slow_mo=settings.PLAYWRIGHT_SLOW_MO,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                # viewport=settings.PLAYWRIGHT_VIEWPORT,
                # Assuming this is in settings e.g. {'width': 1280, 'height': 720} or None
                # args=["--disable-blink-features=AutomationControlled"] # Optional: may help avoid bot detection
            )
            self.browser.set_default_timeout(settings.PLAYWRIGHT_TIMEOUT)  # e.g. 30000ms

            # A new persistent context usually comes with one page. Use it or create one.
            self.page = self.browser.pages[0] if self.browser.pages else self.browser.new_page()
            print(
                f"Persistent context for '{account_to_use.username}' is active. Page {'retrieved' if self.browser.pages else 'created'}.")
            # DO NOT set self._logged_in_account here. Login method must confirm login first.

        # If context exists but page is somehow closed or None (should be rare if above logic is sound)
        if not self.page or self.page.is_closed():
            if not self.browser or not self.browser.is_connected():
                # This should have been caught by 'must_launch_new_or_switch_context'
                print("Error: Browser not connected when trying to get/create a new page. Re-evaluating context.")
                # Force re-evaluation by calling self recursively, this time it should hit the launch logic
                # This is a safeguard, ideally not hit.
                return self._ensure_browser_page(for_account=account_to_use)

            print("Page was closed or None in an existing context. Creating a new page.")
            self.page = self.browser.new_page()

        return self.page

    def login(self, account: Account) -> bool:
        """
        Logs into Xiaohongshu. Tries persistent context first, then falls back to QR code scan.
        """
        try:
            # Ensure page and browser are set up for the specific account being logged in.
            self.page = self._ensure_browser_page(for_account=account)
        except ValueError as ve:
            print(f"Error setting up browser page: {ve}")
            return False

        page = self.page  # convenience
        assert page is not None, "Page should be initialized by _ensure_browser_page"
        assert self.browser is not None, "Browser context should be initialized by _ensure_browser_page"

        is_logged_in_via_persistence = False
        profile_url = f"{self.BASE_URL}/user/profile/64cf0d8e000000000e026341"  # A page that typically requires login

        print(f"Checking login status for {account.username} by navigating to {profile_url}...")
        try:
            page.goto(profile_url, wait_until="networkidle",
                      timeout=settings.PLAYWRIGHT_TIMEOUT)  # e.g. 15000ms for navigation
            current_url = page.url
            print(f"Current URL after navigating to profile: {current_url}")

            # CRITICAL: Login Verification Logic. This needs robust selectors for Xiaohongshu.
            # Check if not redirected to a login page and if user-specific elements are present.
            if profile_url.split("?")[0] in current_url and not any(
                    sub in current_url for sub in ["/login", "/unlogin"]):
                # Placeholder: Check for known elements that only appear when logged in.
                # These selectors are GUESSES and MUST be verified/updated for Xiaohongshu.
                # Example: Looking for user avatar, "Edit Profile" button, or other user-specific content.
                # Original code had: page.query_selector("//div[contains(@class, 'avatar-container')]//img[@alt='avatar']")
                # More examples (these are illustrative, not guaranteed to work):
                # - page.is_visible("text='编辑资料'")
                # - page.query_selector("a[href*='/me/settings']")
                # - page.query_selector("img.user-avatar")
                if page.query_selector("//div[contains(@class, 'avatar-container')]//img[@alt='avatar']") or \
                        page.is_visible("text='编辑资料'") or \
                        page.query_selector(
                            "a[href*='/user/profile/'] /*[self::span or self::div][contains(text(),'笔记') or contains(text(),'收藏') or contains(text(),'赞过')]"):  # Checking for Profile tabs like Notes, Collections, Liked
                    print(
                        f"Login for {account.username} appears to be active via persistent context (found indicative logged-in elements).")
                    is_logged_in_via_persistence = True
                else:
                    print(
                        f"On profile-like URL for {account.username} ({current_url}), but specific logged-in elements not found. Assuming not logged in via persistence.")
            else:
                print(
                    f"Redirected or URL mismatch for {account.username}. Current URL: {current_url}. Expected profile URL: {profile_url}. Assuming not logged in via persistence.")

        except Exception as e:
            print(f"Error during persistent context login check for {account.username}: {e}. Proceeding to QR scan.")
            # Ensure page is still usable for QR login attempt, might need a refresh or goto login page.
            try:
                if not page.url.startswith(f"{self.BASE_URL}/login"):
                    page.goto(f"{self.BASE_URL}/login", wait_until="domcontentloaded",
                              timeout=settings.PLAYWRIGHT_TIMEOUT)
            except Exception as e_nav:
                print(f"Failed to navigate to login page for QR scan after error: {e_nav}")
                return False

        if is_logged_in_via_persistence:
            self._logged_in_account = account  # Set the successfully logged-in account
            print(f"Login verified for {account.username} using persistent context.")
            # No explicit cookie saving here, relying on persistent context
            # if account.cookies_file: # User commented this out, respecting the change direction
            #     try:
            #         self.auth_manager.save_cookies(self.browser, account.cookies_file)  # self.browser is BrowserContext
            #         print(f"Cookies for {account.username} also saved to {account.cookies_file}.")
            #     except Exception as e:
            #         print(f"Failed to save cookies to {account.cookies_file} after persistent login: {e}")
            return True

        print(
            f"Login with persistent context failed or not detected for {account.username}. Proceeding to manual QR Scan...")
        try:
            if not page.url.startswith(f"{self.BASE_URL}/login"):  # Ensure we are on login page for QR
                page.goto(f"{self.BASE_URL}/login", wait_until="domcontentloaded", timeout=settings.PLAYWRIGHT_TIMEOUT)
        except Exception as e:
            print(f"Failed to navigate to login page for QR scan: {e}")
            return False

        print(
            "Please scan the QR code on the Xiaohongshu login page in the browser within the timeout period (e.g., 60 seconds).")
        try:
            # Wait for user to scan QR code and for navigation to a logged-in page
            qr_scan_timeout = getattr(settings, 'LOGIN_QR_TIMEOUT', 60000)  # Use setting or default to 60s
            page.wait_for_url(
                lambda url: any(sub in url for sub in ["/explore", "/home", "/me/profile"]) and not "/login" in url,
                timeout=qr_scan_timeout
            )
            print("QR Login successful (detected navigation to a logged-in area).")
            self._logged_in_account = account  # Set the successfully logged-in account

            # No explicit cookie saving here, relying on persistent context.
            # User commented out the original cookie saving logic here as well.
            # if account.cookies_file:
            #     self.auth_manager.save_cookies(self.browser, account.cookies_file)
            # else:
            #     # Generate a cookie file name if not provided
            #     generated_cookie_file = self.auth_manager.get_cookies_path(
            #         f"{account.username}_{self.platform_name.lower()}_cookies.json")
            #     print(f"Account.cookies_file not set, will attempt to save to: {generated_cookie_file}")
            #     self.auth_manager.save_cookies(self.browser, generated_cookie_file)
            # Consider updating account object: account.cookies_file = str(generated_cookie_file) if you want it to persist on the object

            return True
        except Exception as e:
            print(f"QR Login failed or timed out: {e}")
            # Clear _logged_in_account if login attempt failed to avoid inconsistent state
            if self._logged_in_account == account:  # Only clear if it was tentatively set to this account
                self._logged_in_account = None
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
            print(
                f"Account {account.username} is not the currently logged-in user ({self._logged_in_account.username if self._logged_in_account else 'None'}). Please login with the correct account first.")
            # Optionally, could attempt self.login(account) here if desired.
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
            print(
                f"Account {account.username} is not the currently logged-in user ({self._logged_in_account.username if self._logged_in_account else 'None'}). Please login with the correct account first.")
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
                print(
                    f"Xiaohongshu browser context for '{self._logged_in_account.username if self._logged_in_account else 'Unknown User'}' closed.")
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
                pass  # Playwright cleanup is tricky when not using 'with' statement.
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
        "password": "dummy_password",  # Not used for QR login
        "cookies_file": "test_xhs_user_xiaohongshu_cookies.json"  # Will be created if login is successful
    }
    test_account = Account(**test_account_details)

    # Ensure data/cookies directory exists (settings should handle this, but double check for standalone test)
    if settings.COOKIES_DIR:
        Path(settings.COOKIES_DIR).mkdir(parents=True, exist_ok=True)
    else:
        print("Warning: settings.COOKIES_DIR is not defined. Cookie and user data paths might be relative.")
        Path("data/cookies").mkdir(parents=True, exist_ok=True)  # Default if not in settings

    # Create a dummy user_data directory for testing if it doesn't exist
    # The _get_user_data_dir method will create account-specific subdirs
    dummy_base_user_data_path = Path(
        settings.COOKIES_DIR).parent / "browser_user_data" if settings.COOKIES_DIR else Path("data/browser_user_data")
    dummy_base_user_data_path.mkdir(parents=True, exist_ok=True)

    xhs_platform = None
    try:
        with sync_playwright() as p_instance:
            xhs_platform = XiaohongshuPlatform(playwright_instance=p_instance)
            print(f"Attempting to login with account: {test_account.username}")
            login_success = xhs_platform.login(test_account)

            if login_success:
                print(f"Login successful for {test_account.username}.")

                # --- Test Search (will print 'not implemented') ---
                print("\nTesting post search...")
                posts = xhs_platform.search_posts(keywords=["学英语"], count=2)
                if posts:
                    for post in posts:
                        print(f"  Found post: {post.title} ({post.url})")
                else:
                    print("  No posts found or search not fully implemented.")

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
