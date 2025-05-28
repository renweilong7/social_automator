# accounts/models.py
# 定义 Account 类，包含用户名、密码（或token）、平台类型等。
# 使用 Pydantic 可以方便地进行数据校验。

from typing import Optional, Dict, Any
from pydantic import BaseModel, SecretStr

class Account(BaseModel):
    username: str
    password: Optional[SecretStr] = None  # Use SecretStr for sensitive data
    token: Optional[str] = None
    platform: str  # e.g., "xiaohongshu", "weibo"
    cookies_file: Optional[str] = None # e.g., "user1_xiaohongshu_cookies.json"

    class Config:
        # Pydantic config if needed, e.g., for ORM mode or custom validation
        pass

class BrowserAccount(BaseModel):
    """Represents a browser profile with its own user data directory."""
    username: str  # Name for this browser profile/configuration
    user_data_dir: str  # Path to the user data directory for this browser profile
    config: Dict[str, Any] = {}  # Optional extra configuration

    class Config:
        pass

if __name__ == '__main__':
    # Example Usage (for testing purposes)
    try:
        account_data_valid = {
            "username": "test_user",
            "password": "supersecret",
            "platform": "xiaohongshu",
            "cookies_file": "test_user_xiaohongshu.json"
        }
        account1 = Account(**account_data_valid)
        print(f"Valid Account 1: {account1.model_dump(exclude={'password'})}")
        if account1.password:
            print(f"Account 1 Password (actual value): {account1.password.get_secret_value()}")

        account_data_token = {
            "username": "token_user",
            "token": "abcdef123456",
            "platform": "custom_api",
        }
        account2 = Account(**account_data_token)
        print(f"Valid Account 2: {account2.model_dump()}")

        account_data_invalid = {
            "username": "invalid_user" # Missing platform
        }
        # This should raise a validation error
        # account_invalid = Account(**account_data_invalid)
        # print(account_invalid)

        # Example Usage for BrowserAccount
        browser_account_data = {
            "username": "main_browser_profile",
            "user_data_dir": "data/browser_profiles/main_profile",
            "config": {"theme": "dark", "extensions_enabled": True}
        }
        browser_acc1 = BrowserAccount(**browser_account_data)
        print(f"Browser Account 1: {browser_acc1.model_dump()}")

        browser_account_data_minimal = {
            "username": "secondary_profile",
            "user_data_dir": "data/browser_profiles/secondary_profile",
        }
        browser_acc2 = BrowserAccount(**browser_account_data_minimal)
        print(f"Browser Account 2 (minimal): {browser_acc2.model_dump()}")

    except Exception as e:
        print(f"Error during Account model testing: {e}")