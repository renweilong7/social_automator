# tasks/workflow.py
# 定义核心的自动化流程。

from typing import Optional, Dict, Any
import logging

# Assuming other modules are structured as per the plan
from social_automator.config.user_config_manager import UserConfigManager, TargetConfig
from social_automator.accounts.account_manager import AccountManager
from social_automator.accounts.models import Account
from social_automator.platforms.base_platform import BasePlatform, PostData
from social_automator.platforms.xiaohongshu import XiaohongshuPlatform
# from social_automator.platforms.weibo import WeiboPlatform # If/when implemented
from social_automator.llm.generator import ContentGenerator
from social_automator.utils.logger import setup_logger # Assuming logger is configured here

# Setup logger for this module
# The name 'workflow_logger' can be customized. 
# If setup_logger configures the root logger, direct logging.info etc. might be sufficient.
logger = setup_logger('workflow_logger', 'workflow.log') # Example: logs to 'workflow.log'
# Or, if setup_logger is called once in main_cli.py to configure root:
# logger = logging.getLogger(__name__)

class AutomationWorkflow:
    def __init__(
        self,
        config_manager: UserConfigManager,
        account_manager: AccountManager,
        content_generator: ContentGenerator
        # platform_factory: Callable[[str], BasePlatform] # Optional: a factory for platforms
    ):
        self.config_manager = config_manager
        self.account_manager = account_manager
        self.content_generator = content_generator
        # self.platform_factory = platform_factory
        self.platform_instances: Dict[str, BasePlatform] = {} # Cache for platform instances
        logger.info("AutomationWorkflow initialized.")

    def _get_platform_instance(self, platform_name: str) -> Optional[BasePlatform]:
        """Gets or creates a platform instance."""
        platform_name_lower = platform_name.lower()
        if platform_name_lower in self.platform_instances:
            return self.platform_instances[platform_name_lower]

        # Platform Factory Logic (simple version)
        # In a more complex app, this could be a dedicated factory class or function.
        platform_instance: Optional[BasePlatform] = None
        if platform_name_lower == "xiaohongshu":
            # Assuming Playwright instance management is handled within XiaohongshuPlatform
            # or passed globally if needed.
            platform_instance = XiaohongshuPlatform() 
        # elif platform_name_lower == "weibo":
        #     platform_instance = WeiboPlatform()
        else:
            logger.error(f"Unsupported platform: {platform_name}")
            return None
        
        if platform_instance:
            self.platform_instances[platform_name_lower] = platform_instance
        return platform_instance

    def run_automation_task(
        self, 
        platform_name: str, 
        target_product_service: str, 
        action: str = "comment" # or "post"
    ) -> None:
        """
        Executes a full automation task for a given platform and target product/service.

        Args:
            platform_name (str): The name of the platform (e.g., "xiaohongshu").
            target_product_service (str): The name of the product/service from targets_keywords.json.
            action (str): The action to perform ("comment" or "post").
        """
        logger.info(f"Starting automation task: Platform='{platform_name}', Target='{target_product_service}', Action='{action}'")

        # 1. Get Target Configuration
        target_config: Optional[TargetConfig] = self.config_manager.get_target(target_product_service)
        if not target_config:
            logger.error(f"Target configuration for '{target_product_service}' not found. Aborting task.")
            return
        logger.info(f"Loaded target config: {target_config.product_service}, Keywords: {target_config.keywords}")

        # 2. Select an Account
        # Simple strategy: find first account matching the platform.
        # More complex: round-robin, least recently used, specific account selection.
        selected_account: Optional[Account] = None
        for acc_data in self.account_manager.list_accounts(): # Assuming list_accounts returns list of Account objects or dicts
            # Ensure acc_data is an Account object or convert it
            current_account = Account(**acc_data) if isinstance(acc_data, dict) else acc_data
            if current_account.platform.lower() == platform_name.lower():
                selected_account = current_account
                break
        
        if not selected_account:
            logger.error(f"No account found for platform '{platform_name}'. Aborting task.")
            return
        logger.info(f"Selected account: {selected_account.username} for platform {platform_name}")

        # 3. Get/Instantiate Platform Object and Login
        platform = self._get_platform_instance(platform_name)
        if not platform:
            logger.error(f"Failed to get platform instance for '{platform_name}'. Aborting task.")
            return

        logger.info(f"Attempting to login to {platform.platform_name} with account {selected_account.username}...")
        login_success = platform.login(selected_account)
        if not login_success:
            logger.error(f"Login failed for account {selected_account.username} on {platform.platform_name}. Aborting task.")
            # platform.close() # Close platform instance if login fails and it was opened
            return
        logger.info(f"Login successful for {selected_account.username} on {platform.platform_name}.")

        try:
            # 4. Platform Actions (Search, Extract)
            # For 'comment' action, we need to find a post to comment on.
            # For 'post' action, we might not need to search first (depends on strategy).
            
            relevant_post_url: Optional[str] = None
            post_summary_for_llm: str = f"General interest post related to {', '.join(target_config.keywords)} on {platform_name}."

            if action == "comment":
                logger.info(f"Searching for posts related to keywords: {target_config.keywords}")
                # Search for posts. We might take the first relevant one.
                # The count can be small if we just need one post.
                found_posts: List[PostData] = platform.search_posts(keywords=target_config.keywords, count=5)
                
                if not found_posts:
                    logger.warning(f"No posts found for keywords: {target_config.keywords} on {platform.platform_name}. Cannot proceed with commenting.")
                    return # Or try different keywords, or switch to 'post' action if configured
                
                # Strategy: pick the first post found. Could be more sophisticated.
                target_post = found_posts[0]
                relevant_post_url = str(target_post.url) # Ensure it's a string
                logger.info(f"Selected post for commenting: {relevant_post_url} (Title: {target_post.title})")

                # Extract some details for LLM context if needed (optional, could use title/snippet from search)
                # post_details = platform.extract_post_details(relevant_post_url)
                # if post_details and post_details.full_content:
                #     post_summary_for_llm = post_details.full_content[:500] # Truncate for LLM
                # elif target_post.content_snippet:
                #     post_summary_for_llm = target_post.content_snippet
                # elif target_post.title:
                #     post_summary_for_llm = target_post.title
                # else:
                #     logger.warning("Could not get a good summary for the selected post.")
                # Simplified summary for now:
                post_summary_for_llm = f"A post titled '{target_post.title}' about '{', '.join(target_config.keywords)}'."

            # 5. Generate Content with LLM
            generated_content: Optional[str] = None
            logger.info("Generating content with LLM...")

            if action == "comment":
                if not relevant_post_url: # Should have been set if action is comment and posts were found
                    logger.error("No relevant post URL to comment on. Aborting comment generation.")
                    return

                generated_content = self.content_generator.generate_promotional_comment(
                    post_summary=post_summary_for_llm,
                    product_name=target_config.product_service,
                    product_features=target_config.core_sell_points or "great features",
                    target_audience=target_config.target_audience or "everyone",
                    language="Chinese" # Or make this configurable
                )
            elif action == "post":
                generated_content = self.content_generator.generate_post_draft(
                    topic=f"About {target_config.product_service} and its benefits for {target_config.target_audience}",
                    product_name=target_config.product_service,
                    core_sell_points=target_config.core_sell_points or "Key benefits here",
                    target_audience=target_config.target_audience or "potential users",
                    keywords=target_config.keywords,
                    platform=platform.platform_name,
                    language="Chinese" # Or make this configurable
                )
            else:
                logger.error(f"Unknown action: '{action}'. Supported actions are 'comment' or 'post'.")
                return

            if not generated_content:
                logger.error("LLM failed to generate content. Aborting task.")
                return
            logger.info(f"LLM generated content (first 100 chars): '{generated_content[:100]}...' ")

            # 6. Publish Content
            publish_success = False
            if action == "comment":
                if relevant_post_url:
                    logger.info(f"Publishing comment to {relevant_post_url}...")
                    publish_success = platform.publish_comment(relevant_post_url, generated_content, selected_account)
            elif action == "post":
                logger.info(f"Publishing new post...")
                # Post content structure might vary. For now, assume text content.
                # A more robust system would define this structure per platform or in LLM output.
                post_payload = {"text": generated_content, "title": f"Check out {target_config.product_service}!"} # Example payload
                publish_success = platform.publish_post(post_payload, selected_account)
            
            if publish_success:
                logger.info(f"Action '{action}' performed successfully on {platform.platform_name} for target '{target_product_service}'.")
            else:
                logger.error(f"Failed to perform action '{action}' on {platform.platform_name}.")

        except Exception as e:
            logger.error(f"An unexpected error occurred during the automation task: {e}", exc_info=True)
        finally:
            # 7. Close platform resources (e.g., browser)
            # Consider if platform instances should be long-lived or closed after each task.
            # If they are cached in self.platform_instances, closing them here means they need re-init and re-login next time.
            # For now, let's close it. A more sophisticated manager might keep them open if tasks are frequent.
            if platform_name.lower() in self.platform_instances:
                logger.info(f"Closing platform instance for {platform_name}...")
                self.platform_instances[platform_name.lower()].close()
                del self.platform_instances[platform_name.lower()]
            logger.info(f"Automation task for '{target_product_service}' on '{platform_name}' finished.")

# Example of how this workflow might be invoked (typically from main_cli.py or a scheduler)
if __name__ == '__main__':
    # This is a simplified setup for demonstration. 
    # In a real app, these would be initialized properly with paths from settings.
    
    # --- Mock/Dummy Initializations (replace with actuals from your project structure) ---
    # 1. Setup a basic logger for the demo if not already done by importing setup_logger
    #    If setup_logger in utils.logger configures the root logger, this might not be needed here.
    #    For this __main__, let's ensure some logging output is visible.
    if not logging.getLogger().hasHandlers(): # Check if root logger is already configured
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logger.info("Starting workflow __main__ demo.")

    # Create dummy data files if they don't exist (for standalone testing)
    from pathlib import Path
    from social_automator.config.settings import settings # For default paths
    import json

    # Dummy accounts.json
    if not settings.ACCOUNTS_FILE.exists():
        settings.ACCOUNTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        dummy_accounts = [
            {"platform": "xiaohongshu", "username": "test_xhs_user", "password": "unused", "cookies_file": "test_xhs_user_xiaohongshu_cookies.json"}
        ]
        with open(settings.ACCOUNTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(dummy_accounts, f, indent=2)
        logger.info(f"Created dummy accounts file: {settings.ACCOUNTS_FILE}")

    # Dummy targets_keywords.json
    if not settings.TARGETS_KEYWORDS_FILE.exists():
        settings.TARGETS_KEYWORDS_FILE.parent.mkdir(parents=True, exist_ok=True)
        dummy_targets = [
            {"product_service": "记账app test", "keywords": ["记账app推荐", "好用的记账软件"], "core_sell_points": "简洁易用，自动同步", "target_audience": "学生和年轻白领"}
        ]
        with open(settings.TARGETS_KEYWORDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(dummy_targets, f, indent=2, ensure_ascii=False)
        logger.info(f"Created dummy targets file: {settings.TARGETS_KEYWORDS_FILE}")

    # Initialize managers and generator
    try:
        config_mngr = UserConfigManager(config_file_path=settings.TARGETS_KEYWORDS_FILE)
        account_mngr = AccountManager(accounts_file_path=settings.ACCOUNTS_FILE)
        # LLM Generator - requires OPENAI_API_KEY or passed key
        # For this demo, it might fail if API key is not set, but workflow structure can be seen.
        try:
            content_gen = ContentGenerator() # Assumes OPENAI_API_KEY is in env
        except Exception as e:
            logger.error(f"Failed to initialize ContentGenerator (LLM API key might be missing): {e}")
            logger.warning("LLM-dependent parts of the workflow will likely fail.")
            # Create a mock generator if real one fails, to test workflow structure
            class MockContentGenerator:
                def generate_promotional_comment(self, **kwargs): return "Mocked promotional comment."
                def generate_post_draft(self, **kwargs): return "Mocked post draft."
            content_gen = MockContentGenerator()

        # Initialize Workflow
        workflow_runner = AutomationWorkflow(config_mngr, account_mngr, content_gen)

        # --- Run a Test Task ---
        # This will attempt a full flow. XiaohongshuPlatform parts are placeholders/require manual login.
        logger.info("\n--- Running a test automation task for Xiaohongshu (comment) ---")
        # Note: XiaohongshuPlatform's methods (search, publish) are mostly placeholders.
        # The login part might require manual QR scan if cookies aren't pre-existing and valid.
        workflow_runner.run_automation_task(
            platform_name="xiaohongshu",
            target_product_service="记账app test",
            action="comment" # or "post"
        )
        logger.info("\nWorkflow __main__ demo finished.")

    except ImportError as e:
        logger.error(f"ImportError during __main__ setup: {e}. Ensure all modules are correctly placed and Python path is set up.")
    except Exception as e:
        logger.error(f"An unexpected error in __main__ demo: {e}", exc_info=True)