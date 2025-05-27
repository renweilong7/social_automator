# main_cli.py
# 使用 argparse 或 click 库创建命令行接口。
# 用户可以通过命令行参数手动触发任务，例如 python -m social_automator.main_cli run-task --platform xiaohongshu --target "记账app test"。
# 负责初始化各个模块（日志、配置、账号管理器等）。

import argparse
import sys
from pathlib import Path

# Ensure the project root is in PYTHONPATH to allow absolute imports
# This is often handled by how you run the script (e.g., python -m social_automator.main_cli)
# or by setting PYTHONPATH environment variable.
# If running `python social_automator/main_cli.py` directly from project root, this might be needed:
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT.parent) not in sys.path: # If social_automator is a sub-package
    sys.path.insert(0, str(PROJECT_ROOT.parent))


from config.settings import AppSettings
from utils.logger import setup_logger, DEFAULT_LOGS_DIR, DEFAULT_LOG_LEVEL
from accounts.account_manager import AccountManager
from config.user_config_manager import UserConfigManager
from llm.generator import ContentGenerator
from tasks.workflow import AutomationWorkflow
from platforms.base_platform import PlatformNotSupportedError

# Initialize settings first as other modules might depend on it
# This will also load .env and create necessary directories
settings = AppSettings()

# Setup a global logger for the CLI application
# The name 'main_cli' will appear in log messages from this file.
logger = setup_logger(
    logger_name='main_cli',
    log_file_name='cli_app.log', # Specific log file for CLI operations
    level=settings.LOGGING_LEVEL or DEFAULT_LOG_LEVEL,
    logs_dir=settings.LOGS_DIR or DEFAULT_LOGS_DIR
)

def run_automation_task_cli(args):
    """
    Handles the 'run-task' command from the CLI.
    """
    logger.info(f"CLI: Received 'run-task' command. Platform: {args.platform}, Target: '{args.target_product_service}'")

    try:
        # Initialize core components
        logger.debug("Initializing AccountManager...")
        account_manager = AccountManager(accounts_file=settings.ACCOUNTS_FILE)
        
        logger.debug("Initializing UserConfigManager...")
        user_config_manager = UserConfigManager(config_file=settings.TARGETS_KEYWORDS_FILE)
        
        logger.debug("Initializing ContentGenerator...")
        content_generator = ContentGenerator(
            api_key=settings.OPENAI_API_KEY,
            model_name=settings.LLM_MODEL_NAME
        )
        
        logger.debug("Initializing AutomationWorkflow...")
        workflow = AutomationWorkflow(
            user_config_manager=user_config_manager,
            account_manager=account_manager,
            content_generator=content_generator,
            settings=settings
        )

        logger.info(f"Attempting to run automation for platform '{args.platform}' and target '{args.target_product_service}'")
        workflow.run_automation_task(
            platform_name=args.platform,
            target_product_service_name=args.target_product_service,
            task_type=args.task_type # 'comment' or 'post'
        )
        logger.info(f"Automation task for '{args.target_product_service}' on '{args.platform}' completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"Configuration file error: {e}. Please ensure all data files (accounts.json, targets_keywords.json) exist and are correctly configured.")
        print(f"Error: {e}. Check log for details.", file=sys.stderr)
        sys.exit(1)
    except PlatformNotSupportedError as e:
        logger.error(f"Platform error: {e}")
        print(f"Error: {e}. Supported platforms might be 'xiaohongshu', 'weibo', etc.", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Value error during task execution: {e}")
        print(f"Error: {e}. Check your input or configuration.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred during the automation task: {e}", exc_info=True)
        print(f"An unexpected error occurred: {e}. Check 'cli_app.log' and other logs for details.", file=sys.stderr)
        sys.exit(1)

def main():
    """
    Main function to parse arguments and dispatch commands.
    """
    parser = argparse.ArgumentParser(description="Social Media Automator CLI")
    subparsers = parser.add_subparsers(title="commands", dest="command", help="Available commands")
    subparsers.required = True # Make sure a subcommand is given

    # --- 'run-task' command --- 
    run_task_parser = subparsers.add_parser("run-task", help="Run a specific automation task.")
    run_task_parser.add_argument(
        "--platform", 
        type=str, 
        required=True, 
        help="The social media platform to target (e.g., 'xiaohongshu', 'weibo')."
    )
    run_task_parser.add_argument(
        "--target", 
        dest="target_product_service",
        type=str, 
        required=True, 
        help="The name of the product/service to automate for (must match an entry in targets_keywords.json)."
    )
    run_task_parser.add_argument(
        "--task-type",
        dest="task_type",
        type=str,
        choices=['comment', 'post'],
        default='comment', # Default to creating comments
        help="The type of task to perform: 'comment' (find posts and comment) or 'post' (create a new post). Default: 'comment'."
    )
    run_task_parser.set_defaults(func=run_automation_task_cli)

    # --- (Future commands can be added here) ---
    # Example: Add account command
    # add_account_parser = subparsers.add_parser("add-account", help="Add a new social media account.")
    # add_account_parser.add_argument("--platform", required=True, help="Platform name")
    # add_account_parser.add_argument("--username", required=True, help="Account username")
    # # ... other account fields ...
    # add_account_parser.set_defaults(func=add_account_cli) # Define add_account_cli function

    args = parser.parse_args()
    
    logger.info(f"CLI started with arguments: {vars(args)}")
    
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    # This allows running the CLI using `python social_automator/main_cli.py ...`
    # For module execution `python -m social_automator.main_cli ...`, the if block is also fine.
    main()

    # Example CLI Usages (run from the project root directory, e.g., `e:\workspace\social_automator`):
    # Ensure .env, data/accounts.json, data/targets_keywords.json are set up.

    # 1. Run a commenting task for '记账app test' on Xiaohongshu:
    # python -m social_automator.main_cli run-task --platform xiaohongshu --target "记账app test"
    # (or `python social_automator/main_cli.py run-task --platform xiaohongshu --target "记账app test"`)

    # 2. Run a posting task for '记账app test' on Xiaohongshu:
    # python -m social_automator.main_cli run-task --platform xiaohongshu --target "记账app test" --task-type post

    # 3. Run a task for a non-existent target (should error gracefully):
    # python -m social_automator.main_cli run-task --platform xiaohongshu --target "NonExistentProduct"

    # 4. Run a task for an unsupported platform (should error gracefully):
    # python -m social_automator.main_cli run-task --platform faketagram --target "记账app test"

    # To test, you'd need to:
    # 1. Create a .env file with OPENAI_API_KEY.
    # 2. Create data/accounts.json with at least one Xiaohongshu account.
    #    Example: `[{"platform": "xiaohongshu", "username": "testuser", "password": "testpass", "token": null, "cookies_file": null}]`
    # 3. Create data/targets_keywords.json with a target.
    #    Example: `[{"product_service": "记账app test", "keywords": ["记账app推荐"], "core_sell_points": "简洁易用", "target_audience": "学生"}]`
    # 4. (Optional) Implement actual login/search/post logic in xiaohongshu.py if not using placeholders.