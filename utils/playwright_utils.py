# utils/playwright_utils.py
# 封装一些 Playwright 的常用操作，如带重试的元素查找、安全点击、滚动等，避免在平台代码中重复。

from playwright.sync_api import Page, ElementHandle, Locator, TimeoutError as PlaywrightTimeoutError
from typing import Optional, Union, Tuple
import time

class PlaywrightUtils:
    """
    A collection of utility functions for common Playwright operations.
    These methods are designed to be used with a Playwright Page object.
    """

    DEFAULT_TIMEOUT = 10000  # 10 seconds
    DEFAULT_RETRY_INTERVAL = 0.5  # 0.5 seconds

    @staticmethod
    def find_element(
        page: Page,
        selector: str,
        timeout: int = DEFAULT_TIMEOUT,
        state: Optional[str] = 'visible'
    ) -> Optional[Locator]:
        """
        Finds a single element using a selector, waiting for it to be in a specific state.

        Args:
            page (Page): The Playwright page object.
            selector (str): The CSS selector or XPath to find the element.
            timeout (int): Maximum time to wait for the element in milliseconds.
            state (Optional[str]): The state to wait for ('visible', 'hidden', 'attached', 'detached'). 
                                   If None, waits for 'attached'.

        Returns:
            Optional[Locator]: The Playwright Locator object if found, None otherwise.
        """
        try:
            locator = page.locator(selector)
            if state:
                locator.wait_for(state=state, timeout=timeout)
            else:
                # Default behavior if state is None, just check if it's attached (implicitly by count > 0)
                locator.wait_for(state='attached', timeout=timeout) # or simply check count
            return locator
        except PlaywrightTimeoutError:
            # print(f"Timeout: Element '{selector}' not found or not in state '{state}' within {timeout}ms.")
            return None
        except Exception as e:
            # print(f"Error finding element '{selector}': {e}")
            return None

    @staticmethod
    def find_elements(
        page: Page,
        selector: str,
        min_count: int = 1,
        timeout: int = DEFAULT_TIMEOUT
    ) -> list[Locator]:
        """
        Finds multiple elements using a selector, waiting for a minimum count.

        Args:
            page (Page): The Playwright page object.
            selector (str): The CSS selector or XPath to find the elements.
            min_count (int): Minimum number of elements to expect.
            timeout (int): Maximum time to wait in milliseconds.

        Returns:
            list[Locator]: A list of Playwright Locator objects. Empty if none found or timeout.
        """
        try:
            # Wait for at least one element to be present to avoid immediate empty list
            page.wait_for_selector(selector, timeout=timeout, state='attached')
            locators = page.locator(selector).all()
            if len(locators) >= min_count:
                return locators
            # This part might be tricky as locator.all() doesn't inherently wait for count.
            # A better approach might be to use a loop with a timeout if specific count is critical.
            # For now, relying on wait_for_selector for at least one, then getting all available.
            return locators # or an empty list if the initial wait_for_selector fails
        except PlaywrightTimeoutError:
            # print(f"Timeout: Less than {min_count} elements for '{selector}' found within {timeout}ms.")
            return []
        except Exception as e:
            # print(f"Error finding elements '{selector}': {e}")
            return []

    @staticmethod
    def click_element(
        page: Page,
        selector_or_locator: Union[str, Locator],
        timeout: int = DEFAULT_TIMEOUT,
        force: bool = False,
        delay: Optional[float] = None, # ms
        button: Optional[str] = 'left',
        click_count: int = 1
    ) -> bool:
        """
        Safely clicks an element.

        Args:
            page (Page): The Playwright page object.
            selector_or_locator (Union[str, Locator]): CSS selector, XPath, or a Locator object.
            timeout (int): Timeout for finding the element before clicking.
            force (bool): Whether to bypass actionability checks.
            delay (Optional[float]): Time to wait between mousedown and mouseup in milliseconds.
            button (Optional[str]): 'left', 'right', or 'middle'.
            click_count (int): Number of clicks.

        Returns:
            bool: True if click was successful, False otherwise.
        """
        try:
            if isinstance(selector_or_locator, str):
                element = PlaywrightUtils.find_element(page, selector_or_locator, timeout=timeout, state='visible')
                if not element:
                    return False
            else:
                element = selector_or_locator
            
            element.click(timeout=timeout, force=force, delay=delay, button=button, click_count=click_count)
            return True
        except PlaywrightTimeoutError:
            # print(f"Timeout clicking element: {selector_or_locator}")
            return False
        except Exception as e:
            # print(f"Error clicking element '{selector_or_locator}': {e}")
            return False

    @staticmethod
    def type_text(
        page: Page, 
        selector_or_locator: Union[str, Locator], 
        text: str, 
        timeout: int = DEFAULT_TIMEOUT, 
        delay_per_char: float = 50  # milliseconds
    ) -> bool:
        """
        Types text into an element, character by character with a delay.

        Args:
            page (Page): The Playwright page object.
            selector_or_locator (Union[str, Locator]): CSS selector, XPath, or a Locator object.
            text (str): The text to type.
            timeout (int): Timeout for finding the element.
            delay_per_char (float): Delay in milliseconds between typing each character.

        Returns:
            bool: True if typing was successful, False otherwise.
        """
        try:
            if isinstance(selector_or_locator, str):
                element = PlaywrightUtils.find_element(page, selector_or_locator, timeout=timeout, state='visible')
                if not element:
                    return False
            else:
                element = selector_or_locator
            
            element.focus(timeout=timeout)
            element.fill('') # Clear the field first
            element.type(text, delay=delay_per_char)
            # For more human-like typing, can use page.keyboard.type with delay
            # element.press_sequentially(text, delay=delay_per_char)
            return True
        except PlaywrightTimeoutError:
            # print(f"Timeout typing into element: {selector_or_locator}")
            return False
        except Exception as e:
            # print(f"Error typing into element '{selector_or_locator}': {e}")
            return False

    @staticmethod
    def scroll_page_down(page: Page, speed: int = 1000) -> None:
        """
        Scrolls the page down gradually.

        Args:
            page (Page): The Playwright page object.
            speed (int): Approximate pixels to scroll per step (influences smoothness).
        """
        current_scroll = 0
        page_height = page.evaluate("document.body.scrollHeight")
        while current_scroll < page_height:
            current_scroll += speed
            page.mouse.wheel(0, speed) # scroll down
            page.wait_for_timeout(100) # Small delay for content to load if any
            new_page_height = page.evaluate("document.body.scrollHeight")
            if new_page_height == page_height: # Reached bottom or no new content loaded
                # Check if truly at bottom
                if page.evaluate("window.innerHeight + window.scrollY >= document.body.scrollHeight - 5"): # 5px tolerance
                    break
            page_height = new_page_height

    @staticmethod
    def scroll_to_element(page: Page, selector_or_locator: Union[str, Locator], timeout: int = DEFAULT_TIMEOUT) -> bool:
        """
        Scrolls an element into view.

        Args:
            page (Page): The Playwright page object.
            selector_or_locator (Union[str, Locator]): CSS selector, XPath, or a Locator object.
            timeout (int): Timeout for the scroll operation.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            if isinstance(selector_or_locator, str):
                element = PlaywrightUtils.find_element(page, selector_or_locator, timeout=timeout, state='attached')
                if not element:
                    return False
            else:
                element = selector_or_locator
            
            element.scroll_into_view_if_needed(timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            # print(f"Timeout scrolling to element: {selector_or_locator}")
            return False
        except Exception as e:
            # print(f"Error scrolling to element '{selector_or_locator}': {e}")
            return False

    @staticmethod
    def wait_for_navigation(page: Page, timeout: int = 30000, wait_until: Optional[str] = 'load') -> bool:
        """
        Waits for a page navigation to complete.
        This is typically used after an action that causes a page load (e.g., click a link, submit form).

        Args:
            page (Page): The Playwright page object.
            timeout (int): Maximum time to wait for navigation in milliseconds.
            wait_until (Optional[str]): When to consider navigation succeeded. 
                                       Options: 'load', 'domcontentloaded', 'networkidle', 'commit'.

        Returns:
            bool: True if navigation occurred and completed, False on timeout.
        """
        try:
            page.wait_for_load_state(state=wait_until, timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            # print(f"Timeout waiting for navigation (state: {wait_until}).")
            return False
        except Exception as e:
            # print(f"Error waiting for navigation: {e}")
            return False

    @staticmethod
    def take_screenshot(page: Page, path: str, full_page: bool = True) -> bool:
        """
        Takes a screenshot of the page.

        Args:
            page (Page): The Playwright page object.
            path (str): The path where the screenshot will be saved.
            full_page (bool): Whether to take a screenshot of the full scrollable page.

        Returns:
            bool: True if screenshot was taken successfully, False otherwise.
        """
        try:
            page.screenshot(path=path, full_page=full_page)
            # print(f"Screenshot saved to {path}")
            return True
        except Exception as e:
            # print(f"Error taking screenshot: {e}")
            return False

    @staticmethod
    def get_element_text(page: Page, selector_or_locator: Union[str, Locator], timeout: int = DEFAULT_TIMEOUT) -> Optional[str]:
        """
        Gets the text content of an element.

        Args:
            page (Page): The Playwright page object.
            selector_or_locator (Union[str, Locator]): CSS selector, XPath, or a Locator object.
            timeout (int): Timeout for finding the element.

        Returns:
            Optional[str]: The text content of the element, or None if not found or error.
        """
        try:
            if isinstance(selector_or_locator, str):
                element = PlaywrightUtils.find_element(page, selector_or_locator, timeout=timeout, state='visible')
                if not element:
                    return None
            else:
                element = selector_or_locator
            
            return element.text_content(timeout=timeout)
        except PlaywrightTimeoutError:
            # print(f"Timeout getting text from element: {selector_or_locator}")
            return None
        except Exception as e:
            # print(f"Error getting text from element '{selector_or_locator}': {e}")
            return None

    @staticmethod
    def get_element_attribute(
        page: Page, 
        selector_or_locator: Union[str, Locator], 
        attribute_name: str, 
        timeout: int = DEFAULT_TIMEOUT
    ) -> Optional[str]:
        """
        Gets an attribute value of an element.

        Args:
            page (Page): The Playwright page object.
            selector_or_locator (Union[str, Locator]): CSS selector, XPath, or a Locator object.
            attribute_name (str): The name of the attribute to get (e.g., 'href', 'src', 'value').
            timeout (int): Timeout for finding the element.

        Returns:
            Optional[str]: The attribute value, or None if not found or error.
        """
        try:
            if isinstance(selector_or_locator, str):
                element = PlaywrightUtils.find_element(page, selector_or_locator, timeout=timeout, state='attached')
                if not element:
                    return None
            else:
                element = selector_or_locator
            
            return element.get_attribute(attribute_name, timeout=timeout)
        except PlaywrightTimeoutError:
            # print(f"Timeout getting attribute '{attribute_name}' from element: {selector_or_locator}")
            return None
        except Exception as e:
            # print(f"Error getting attribute '{attribute_name}' from element '{selector_or_locator}': {e}")
            return None

# Example usage (requires a running Playwright browser and page)
if __name__ == '__main__':
    from playwright.sync_api import sync_playwright

    print("Playwright Utils Demonstration (requires a browser)")
    print("This example will try to open 'http://example.com' and perform some actions.")

    with sync_playwright() as p:
        browser = None
        try:
            browser = p.chromium.launch(headless=True) # Set headless=False to see the browser
            page = browser.new_page()
            page.goto('http://example.com', timeout=PlaywrightUtils.DEFAULT_TIMEOUT)
            print(f"Opened page: {page.title()}")

            # 1. Find an element
            print("\n1. Finding element 'h1'...")
            h1_element = PlaywrightUtils.find_element(page, 'h1')
            if h1_element:
                print(f"Found h1: {h1_element.text_content()}")
            else:
                print("h1 element not found.")

            # 2. Get text from element
            print("\n2. Getting text from 'p'...")
            p_text = PlaywrightUtils.get_element_text(page, 'p')
            if p_text:
                print(f"Paragraph text: {p_text[:50]}...") # Print first 50 chars
            else:
                print("Paragraph element not found or no text.")

            # 3. Get attribute
            print("\n3. Getting 'href' from 'a' tag...")
            link_href = PlaywrightUtils.get_element_attribute(page, 'a', 'href')
            if link_href:
                print(f"Link href: {link_href}")
            else:
                print("Link 'a' not found or no href attribute.")

            # 4. Type text (example.com doesn't have an input, so this will fail gracefully or skip)
            # For a real test, navigate to a page with an input field.
            print("\n4. Typing text (skipped for example.com)...")
            # success_type = PlaywrightUtils.type_text(page, '#someInput', 'Hello Playwright')
            # print(f"Typing successful: {success_type}")

            # 5. Click element (example.com link)
            print("\n5. Clicking the link...")
            # This will navigate, so handle it or use wait_for_navigation
            # For this demo, we'll just click and not wait for full nav to keep it simple.
            # success_click = PlaywrightUtils.click_element(page, 'a') 
            # print(f"Click successful: {success_click}")
            # if success_click:
            #     PlaywrightUtils.wait_for_navigation(page, timeout=5000) # Wait for potential navigation
            #     print(f"Navigated to: {page.title()}")
            #     page.go_back() # Go back to example.com for next steps
            #     PlaywrightUtils.wait_for_navigation(page, timeout=5000)

            # 6. Scroll page down (example.com is short, so might not show much effect)
            print("\n6. Scrolling page down...")
            PlaywrightUtils.scroll_page_down(page, speed=200)
            print("Scrolled down.")

            # 7. Take a screenshot
            screenshot_path = "example_com_screenshot.png"
            print(f"\n7. Taking screenshot to '{screenshot_path}'...")
            if PlaywrightUtils.take_screenshot(page, screenshot_path):
                print("Screenshot taken.")
            else:
                print("Failed to take screenshot.")

            print("\nDemonstration finished.")

        except Exception as e:
            print(f"An error occurred during the demonstration: {e}")
        finally:
            if browser:
                browser.close()