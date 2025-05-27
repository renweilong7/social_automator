# config/settings.py
# 加载全局配置，如从 .env 文件读取 API 密钥，定义 Playwright 的 headless 模式、超时时间等。
# 可以使用 python-dotenv 库。

import os
from dotenv import load_dotenv
from pathlib import Path

# Determine the project root directory. 
# Assuming settings.py is in 'social_automator/config/', the project root is two levels up.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load environment variables from .env file in the project root
DOTENV_PATH = PROJECT_ROOT / '.env'
load_dotenv(dotenv_path=DOTENV_PATH)

class AppSettings:
    # API Keys (examples, replace with your actual environment variable names)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "your_default_openai_key_if_not_set")
    # Add other API keys as needed
    # SOME_OTHER_API_KEY: str = os.getenv("SOME_OTHER_API_KEY")

    # Playwright Settings
    PLAYWRIGHT_HEADLESS: bool = os.getenv("PLAYWRIGHT_HEADLESS", "True").lower() == "true"
    PLAYWRIGHT_TIMEOUT: int = int(os.getenv("PLAYWRIGHT_TIMEOUT", "30000")) # Default 30 seconds
    PLAYWRIGHT_SLOW_MO: int = int(os.getenv("PLAYWRIGHT_SLOW_MO", "50")) # Milliseconds, 0 for no slow mo

    # Data paths (relative to project root)
    DATA_DIR: Path = PROJECT_ROOT / "data"
    ACCOUNTS_FILE: Path = DATA_DIR / "accounts.json"
    COOKIES_DIR: Path = DATA_DIR / "cookies"
    TARGETS_KEYWORDS_FILE: Path = DATA_DIR / "targets_keywords.json"
    LOGS_DIR: Path = PROJECT_ROOT / "logs" # Logs directory at project root

    # LLM Settings
    LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "gpt-3.5-turbo")

    # Other application settings
    DEFAULT_LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    def __init__(self):
        # Create data directories if they don't exist
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.COOKIES_DIR.mkdir(parents=True, exist_ok=True)
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Instantiate settings to be imported by other modules
settings = AppSettings()

if __name__ == '__main__':
    print("Application Settings:")
    print(f"  Project Root: {PROJECT_ROOT}")
    print(f"  .env Path: {DOTENV_PATH}")
    print(f"  OpenAI API Key Loaded: {'Yes' if settings.OPENAI_API_KEY != 'your_default_openai_key_if_not_set' else 'No (using default or not set)'}")
    print(f"  Playwright Headless: {settings.PLAYWRIGHT_HEADLESS}")
    print(f"  Playwright Timeout: {settings.PLAYWRIGHT_TIMEOUT}ms")
    print(f"  Playwright Slow Mo: {settings.PLAYWRIGHT_SLOW_MO}ms")
    print(f"  Data Directory: {settings.DATA_DIR}")
    print(f"  Accounts File: {settings.ACCOUNTS_FILE}")
    print(f"  Cookies Directory: {settings.COOKIES_DIR}")
    print(f"  Targets/Keywords File: {settings.TARGETS_KEYWORDS_FILE}")
    print(f"  Logs Directory: {settings.LOGS_DIR}")
    print(f"  LLM Model Name: {settings.LLM_MODEL_NAME}")
    print(f"  Default Log Level: {settings.DEFAULT_LOG_LEVEL}")

    # Example of how to create a .env file if it doesn't exist for testing
    if not DOTENV_PATH.exists():
        print(f"\nNote: .env file not found at {DOTENV_PATH}.")
        print("Consider creating one with your API keys and custom settings, for example:")
        print("OPENAI_API_KEY=your_actual_key_here")
        print("PLAYWRIGHT_HEADLESS=False")