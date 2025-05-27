# utils/file_utils.py
# 封装 JSON 读写等。

import json
from pathlib import Path
from typing import Any, Optional, Union
import os

class FileUtils:
    """
    A collection of utility functions for file operations, primarily JSON handling.
    """

    @staticmethod
    def read_json(file_path: Union[str, Path]) -> Optional[Any]:
        """
        Reads a JSON file and returns its content.

        Args:
            file_path (Union[str, Path]): The path to the JSON file.

        Returns:
            Optional[Any]: The content of the JSON file (usually dict or list), 
                           or None if the file doesn't exist or an error occurs.
        """
        try:
            path = Path(file_path)
            if not path.exists():
                # print(f"Error: File not found at {path}")
                return None
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except json.JSONDecodeError as e:
            # print(f"Error decoding JSON from {file_path}: {e}")
            return None
        except Exception as e:
            # print(f"An unexpected error occurred while reading {file_path}: {e}")
            return None

    @staticmethod
    def write_json(file_path: Union[str, Path], data: Any, indent: Optional[int] = 4) -> bool:
        """
        Writes data to a JSON file.

        Args:
            file_path (Union[str, Path]): The path to the JSON file.
                                         The directory will be created if it doesn't exist.
            data (Any): The data to write (must be JSON serializable).
            indent (Optional[int]): JSON indentation level for pretty printing. 
                                    Set to None for a compact file.

        Returns:
            bool: True if writing was successful, False otherwise.
        """
        try:
            path = Path(file_path)
            # Ensure the directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)
            return True
        except TypeError as e:
            # print(f"Error: Data is not JSON serializable for {file_path}: {e}")
            return False
        except Exception as e:
            # print(f"An unexpected error occurred while writing to {file_path}: {e}")
            return False

    @staticmethod
    def ensure_directory_exists(dir_path: Union[str, Path]) -> bool:
        """
        Ensures that a directory exists, creating it if necessary.

        Args:
            dir_path (Union[str, Path]): The path to the directory.

        Returns:
            bool: True if the directory exists or was created successfully, False otherwise.
        """
        try:
            path = Path(dir_path)
            path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            # print(f"Error creating directory {dir_path}: {e}")
            return False

    @staticmethod
    def delete_file(file_path: Union[str, Path]) -> bool:
        """
        Deletes a file if it exists.

        Args:
            file_path (Union[str, Path]): The path to the file.

        Returns:
            bool: True if the file was deleted or did not exist, False if an error occurred during deletion.
        """
        try:
            path = Path(file_path)
            if path.exists() and path.is_file():
                os.remove(path)
                # print(f"File {path} deleted successfully.")
            elif not path.exists():
                # print(f"File {path} does not exist, no action taken.")
                pass # Considered success if file doesn't exist
            else:
                # print(f"Path {path} is a directory, not a file. Deletion skipped.")
                return False # Or raise error, depending on desired strictness
            return True
        except Exception as e:
            # print(f"Error deleting file {file_path}: {e}")
            return False

# Example usage:
if __name__ == '__main__':
    print("FileUtils Demonstration")

    # Create a temporary directory for testing
    temp_dir = Path(__file__).parent / "temp_file_utils_test"
    FileUtils.ensure_directory_exists(temp_dir)
    print(f"Created temporary directory: {temp_dir}")

    # 1. Write JSON data
    test_data_to_write = {
        "name": "Test User",
        "id": 123,
        "projects": ["Project A", "Project B"],
        "active": True,
        "metadata": {"source": "FileUtils Test", "version": "1.0"}
    }
    json_file_path = temp_dir / "test_output.json"
    print(f"\n1. Writing JSON to: {json_file_path}")
    success_write = FileUtils.write_json(json_file_path, test_data_to_write)
    if success_write:
        print("JSON data written successfully.")
    else:
        print("Failed to write JSON data.")

    # 2. Read JSON data
    print(f"\n2. Reading JSON from: {json_file_path}")
    read_data = FileUtils.read_json(json_file_path)
    if read_data:
        print("JSON data read successfully:")
        # print(json.dumps(read_data, indent=2))
        assert read_data == test_data_to_write, "Data mismatch after read/write!"
        print("Data integrity check passed.")
    else:
        print("Failed to read JSON data or file does not exist.")

    # 3. Test reading a non-existent file
    non_existent_file = temp_dir / "non_existent.json"
    print(f"\n3. Attempting to read non-existent file: {non_existent_file}")
    data_non_existent = FileUtils.read_json(non_existent_file)
    if data_non_existent is None:
        print("Correctly handled non-existent file (returned None).")
    else:
        print(f"Error: Expected None for non-existent file, got: {data_non_existent}")

    # 4. Test writing invalid JSON data (e.g., a class instance not serializable by default)
    class NonSerializable:
        pass
    invalid_data_file = temp_dir / "invalid_data.json"
    print(f"\n4. Attempting to write non-serializable data to: {invalid_data_file}")
    success_invalid_write = FileUtils.write_json(invalid_data_file, NonSerializable())
    if not success_invalid_write:
        print("Correctly handled non-serializable data (write failed).")
    else:
        print("Error: Expected write to fail for non-serializable data.")

    # 5. Test deleting a file
    print(f"\n5. Deleting file: {json_file_path}")
    success_delete = FileUtils.delete_file(json_file_path)
    if success_delete:
        print(f"File {json_file_path} deleted (or did not exist).")
        assert not json_file_path.exists(), "File still exists after deletion attempt!"
    else:
        print(f"Failed to delete {json_file_path}.")
    
    # Attempt to delete again (should be fine)
    success_delete_again = FileUtils.delete_file(json_file_path)
    if success_delete_again:
        print(f"Attempting to delete already deleted file {json_file_path} handled correctly.")

    # Clean up the temporary directory (optional, for manual cleanup)
    # For a real test suite, you might use pytest fixtures for temp dirs.
    # import shutil
    # if temp_dir.exists():
    #     shutil.rmtree(temp_dir)
    #     print(f"\nCleaned up temporary directory: {temp_dir}")

    print("\nFileUtils demonstration finished.")