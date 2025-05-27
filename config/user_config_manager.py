# config/user_config_manager.py
# 负责加载和管理用户在 data/targets_keywords.json 中定义的目标产品/服务及其相关的关键词。

import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel, validator

# Assuming settings.py is in the same directory or accessible via project structure
# If AppSettings is defined in config.settings, you can import it like this:
from .settings import settings # Use relative import if in the same package

class TargetConfig(BaseModel):
    product_service: str
    keywords: List[str]
    core_sell_points: Optional[str] = None
    target_audience: Optional[str] = None
    # Add any other fields you expect in your targets_keywords.json

    @validator('keywords', pre=True, always=True)
    def ensure_keywords_is_list(cls, v):
        if not isinstance(v, list):
            raise ValueError('keywords must be a list')
        if not v: # Ensure keywords list is not empty
            raise ValueError('keywords list cannot be empty')
        return v

class UserConfigManager:
    def __init__(self, config_file_path: Path = settings.TARGETS_KEYWORDS_FILE):
        self.config_file_path = config_file_path
        self.targets: List[TargetConfig] = self._load_targets()

    def _load_targets(self) -> List[TargetConfig]:
        """Loads target configurations from the JSON file."""
        if not self.config_file_path.exists():
            print(f"Warning: Targets file not found at {self.config_file_path}. Returning empty list.")
            # Optionally, create a default empty file
            # with open(self.config_file_path, 'w') as f:
            #     json.dump([], f)
            return []
        
        try:
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            validated_targets = []
            for item_data in data:
                try:
                    target = TargetConfig(**item_data)
                    validated_targets.append(target)
                except Exception as e: # Pydantic's ValidationError is a subclass of Exception
                    print(f"Skipping invalid target item due to validation error: {item_data}. Error: {e}")
            return validated_targets
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {self.config_file_path}: {e}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred while loading targets from {self.config_file_path}: {e}")
            return []

    def get_target(self, product_service_name: str) -> Optional[TargetConfig]:
        """Retrieves a specific target configuration by its product/service name."""
        for target in self.targets:
            if target.product_service == product_service_name:
                return target
        return None

    def list_targets(self) -> List[TargetConfig]:
        """Returns all loaded target configurations."""
        return self.targets

    def add_target(self, target_data: Dict[str, Any]) -> bool:
        """Adds a new target configuration and saves it to the file."""
        try:
            new_target = TargetConfig(**target_data)
            # Check if target with the same product_service name already exists
            if self.get_target(new_target.product_service):
                print(f"Target '{new_target.product_service}' already exists. Use update_target or choose a different name.")
                return False
            
            self.targets.append(new_target)
            self._save_targets()
            print(f"Target '{new_target.product_service}' added successfully.")
            return True
        except Exception as e: # Pydantic's ValidationError
            print(f"Error adding target. Invalid data: {target_data}. Error: {e}")
            return False

    def _save_targets(self):
        """Saves the current list of targets back to the JSON file."""
        try:
            # Convert Pydantic models to dicts for JSON serialization
            targets_data = [target.model_dump() for target in self.targets]
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(targets_data, f, indent=2, ensure_ascii=False)
            print(f"Targets saved to {self.config_file_path}")
        except Exception as e:
            print(f"Error saving targets to {self.config_file_path}: {e}")

if __name__ == '__main__':
    # Ensure the dummy targets_keywords.json exists for testing
    dummy_targets_file = settings.TARGETS_KEYWORDS_FILE
    if not dummy_targets_file.exists():
        print(f"Creating dummy targets file: {dummy_targets_file}")
        dummy_data = [
            {
                "product_service": "记账app test", 
                "keywords": ["记账app推荐", "好用的记账软件"], 
                "core_sell_points": "简洁易用，自动同步", 
                "target_audience": "学生和年轻白领"
            },
            {
                "product_service": "健身追踪器", 
                "keywords": ["智能手环", "运动手表"], 
                "core_sell_points": "心率监测，GPS定位", 
                "target_audience": "健身爱好者"
            }
        ]
        with open(dummy_targets_file, 'w', encoding='utf-8') as f:
            json.dump(dummy_data, f, indent=2, ensure_ascii=False)
    
    config_manager = UserConfigManager()
    print("\nLoaded Targets:")
    for t in config_manager.list_targets():
        print(f"  - {t.product_service}: {t.keywords}")

    print("\nGetting specific target '记账app test':")
    target_app = config_manager.get_target("记账app test")
    if target_app:
        print(f"  Found: {target_app.model_dump_json(indent=2)}")
    else:
        print("  Target '记账app test' not found.")

    print("\nAdding a new target:")
    new_target_data = {
        "product_service": "在线课程平台",
        "keywords": ["学习编程", "数据科学课程"],
        "core_sell_points": "名师指导，实战项目",
        "target_audience": "职场提升人群"
    }
    config_manager.add_target(new_target_data)

    print("\nTargets after adding:")
    for t in config_manager.list_targets():
        print(f"  - {t.product_service}")

    # Clean up dummy file if you want
    # dummy_targets_file.unlink(missing_ok=True)