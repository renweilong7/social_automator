# utils/logger.py
# 配置 logging 模块，设置日志格式、级别、输出到文件和控制台。

import logging
import sys
from pathlib import Path

# Try to import settings to get LOGS_DIR and DEFAULT_LOG_LEVEL
# This creates a potential circular dependency if settings.py imports something from utils
# A common pattern is to have a core_settings.py with basic paths/levels that utils can import,
# or pass configuration to setup_logger.

# For simplicity, let's define defaults here or assume settings are loaded by the time this is called from main.
# Or, make log_dir and level parameters of setup_logger.

# Default log directory (can be overridden by settings)
# Assuming this file is in social_automator/utils/logger.py
# Project root is two levels up from 'utils'
DEFAULT_LOGS_DIR = Path(__file__).resolve().parent.parent / 'logs'
DEFAULT_LOG_LEVEL = "INFO"

# Store configured loggers to avoid adding multiple handlers if called multiple times
_configured_loggers = {}

def setup_logger(
    logger_name: Optional[str] = None, 
    log_file_name: Optional[str] = None, 
    level: str = DEFAULT_LOG_LEVEL,
    logs_dir: Path = DEFAULT_LOGS_DIR,
    console_output: bool = True,
    file_output: bool = True,
    propagate: bool = False # Set to True if you want messages to also go to parent (e.g. root) logger
) -> logging.Logger:
    """
    Configures and returns a logger.

    Args:
        logger_name (Optional[str]): Name of the logger. If None, configures the root logger.
        log_file_name (Optional[str]): Name of the log file. If None and file_output is True,
                                     defaults to logger_name.log or app.log (for root).
        level (str): Logging level (e.g., "INFO", "DEBUG", "ERROR").
        logs_dir (Path): Directory to store log files.
        console_output (bool): Whether to output logs to the console.
        file_output (bool): Whether to output logs to a file.
        propagate (bool): Whether the logger should propagate messages to its parent.
                          Usually False for specific module loggers if root is also configured.

    Returns:
        logging.Logger: The configured logger instance.
    """
    global _configured_loggers

    # Use logger_name for the key to check if already configured, or 'root' for root logger
    config_key = logger_name if logger_name else 'root'
    if config_key in _configured_loggers:
        # print(f"Logger '{config_key}' already configured. Returning existing instance.")
        return _configured_loggers[config_key]

    logger = logging.getLogger(logger_name)
    
    # Ensure logger level is set. String to logging level constant.
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {level}')
    logger.setLevel(numeric_level)

    # Prevent adding multiple handlers if this function is called again for the same logger
    # (though _configured_loggers check should prevent this path mostly)
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console Handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File Handler
    if file_output:
        logs_dir.mkdir(parents=True, exist_ok=True)
        if not log_file_name:
            log_file_name = f"{logger_name if logger_name else 'app'}.log"
        log_file_path = logs_dir / log_file_name
        
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.propagate = propagate
    _configured_loggers[config_key] = logger
    
    # print(f"Logger '{config_key}' configured. Level: {level}. File: {log_file_path if file_output else 'N/A'}")
    return logger

# Example of initializing a default application logger (e.g., the root logger)
# This could be called once when the application starts.
# def initialize_default_app_logger():
#     from social_automator.config.settings import settings # Assuming settings are loaded
#     setup_logger(
#         level=settings.DEFAULT_LOG_LEVEL,
#         logs_dir=settings.LOGS_DIR
#     )
#     logging.info("Default application logger initialized.")

if __name__ == '__main__':
    # --- Test Cases ---
    print("Testing logger setup...")

    # 1. Configure and get the root logger
    print("\n--- Configuring Root Logger ---")
    # Ensure logs directory exists for the test
    test_logs_dir = Path(__file__).resolve().parent.parent / 'logs_test'
    test_logs_dir.mkdir(parents=True, exist_ok=True)

    root_logger = setup_logger(level="DEBUG", logs_dir=test_logs_dir, log_file_name="root_test.log")
    root_logger.debug("This is a debug message from root logger.")
    root_logger.info("This is an info message from root logger.")
    root_logger.warning("This is a warning from root logger.")
    root_logger.error("This is an error from root logger.")

    # 2. Configure and get a specific named logger
    print("\n--- Configuring Named Logger 'MyModule' ---")
    module_logger = setup_logger("MyModule", level="INFO", logs_dir=test_logs_dir, log_file_name="mymodule_test.log")
    module_logger.debug("This debug message from MyModule logger should NOT appear (level INFO).")
    module_logger.info("This is an info message from MyModule logger.")
    module_logger.error("This is an error from MyModule logger.")

    # 3. Get the same logger again (should return existing instance without re-configuring handlers)
    print("\n--- Getting 'MyModule' Logger Again ---")
    module_logger_again = setup_logger("MyModule") # No params, should use existing
    module_logger_again.info("Info message from MyModule logger (obtained again).")
    # Check handler count (should not increase)
    # print(f"MyModule logger handler count: {len(module_logger.handlers)}")

    # 4. Test propagation (if root is configured, messages from child might go to root too if propagate=True)
    print("\n--- Testing Propagation (MyModuleWithPropagate) ---")
    # By default, root_logger (configured above) will handle these if propagated.
    # If root wasn't configured with a console handler, these might only appear in root_test.log.
    propagating_logger = setup_logger(
        "MyModuleWithPropagate", 
        level="DEBUG", 
        logs_dir=test_logs_dir, 
        log_file_name="propagating_test.log",
        propagate=True # Messages will also go to root logger's handlers
    )
    propagating_logger.debug("Debug from propagating_logger (should appear in its file, console via root, and root file).")
    propagating_logger.info("Info from propagating_logger.")

    print("\n--- Testing Logger without File Output ---")
    console_only_logger = setup_logger("ConsoleOnly", file_output=False, level="DEBUG")
    console_only_logger.debug("This message from ConsoleOnly logger should only appear on console.")

    print("\n--- Testing Logger without Console Output (check file) ---")
    file_only_logger = setup_logger("FileOnly", console_output=False, logs_dir=test_logs_dir, log_file_name="file_only_test.log")
    file_only_logger.info("This message from FileOnly logger should only appear in file_only_test.log.")

    print(f"\nLog tests finished. Check console output and log files in: {test_logs_dir.resolve()}")
    print("Files to check: root_test.log, mymodule_test.log, propagating_test.log, file_only_test.log")