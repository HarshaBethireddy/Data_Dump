"""
File utilities for the Enterprise API Testing Framework.

This module provides file operations, path management, and data serialization utilities.
"""

import json
import shutil
import hashlib
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime

from refactored_codebase.utils.logging import get_logger


logger = get_logger(__name__)


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if it doesn't.
    
    Args:
        path: Directory path
        
    Returns:
        Path object
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def safe_file_write(file_path: Union[str, Path], data: Union[str, Dict[str, Any]], encoding: str = 'utf-8') -> None:
    """
    Safely write data to file with atomic operation.
    
    Args:
        file_path: Target file path
        data: Data to write (string or dict for JSON)
        encoding: File encoding
    """
    file_path = Path(file_path)
    temp_path = file_path.with_suffix(f"{file_path.suffix}.tmp")
    
    try:
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to temporary file
        with open(temp_path, 'w', encoding=encoding) as f:
            if isinstance(data, dict):
                json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                f.write(str(data))
        
        # Atomic rename
        temp_path.replace(file_path)
        logger.debug(f"Successfully wrote file: {file_path}")
        
    except Exception as e:
        # Cleanup temp file on error
        if temp_path.exists():
            temp_path.unlink()
        logger.error(f"Failed to write file {file_path}: {e}")
        raise


def safe_file_read(file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
    """
    Safely read file content.
    
    Args:
        file_path: File path to read
        encoding: File encoding
        
    Returns:
        File content as string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        raise


def load_json_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load JSON data from file.
    
    Args:
        file_path: JSON file path
        
    Returns:
        Parsed JSON data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    content = safe_file_read(file_path)
    
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        raise


def save_json_file(file_path: Union[str, Path], data: Dict[str, Any], indent: int = 2) -> None:
    """
    Save data to JSON file.
    
    Args:
        file_path: Target file path
        data: Data to save
        indent: JSON indentation
    """
    safe_file_write(file_path, data)


def calculate_file_hash(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """
    Calculate file hash.
    
    Args:
        file_path: File path
        algorithm: Hash algorithm (md5, sha1, sha256, etc.)
        
    Returns:
        Hex digest of file hash
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_obj = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()


def copy_file_with_backup(source: Union[str, Path], destination: Union[str, Path], backup_suffix: str = '.bak') -> None:
    """
    Copy file with automatic backup of destination.
    
    Args:
        source: Source file path
        destination: Destination file path
        backup_suffix: Backup file suffix
    """
    source = Path(source)
    destination = Path(destination)
    
    if not source.exists():
        raise FileNotFoundError(f"Source file not found: {source}")
    
    # Create backup if destination exists
    if destination.exists():
        backup_path = destination.with_suffix(destination.suffix + backup_suffix)
        shutil.copy2(destination, backup_path)
        logger.debug(f"Created backup: {backup_path}")
    
    # Ensure destination directory exists
    destination.parent.mkdir(parents=True, exist_ok=True)
    
    # Copy file
    shutil.copy2(source, destination)
    logger.debug(f"Copied file: {source} -> {destination}")


def find_files_by_pattern(directory: Union[str, Path], pattern: str, recursive: bool = True) -> List[Path]:
    """
    Find files matching pattern.
    
    Args:
        directory: Directory to search
        pattern: File pattern (glob style)
        recursive: Whether to search recursively
        
    Returns:
        List of matching file paths
    """
    directory = Path(directory)
    
    if not directory.exists():
        return []
    
    if recursive:
        return list(directory.rglob(pattern))
    else:
        return list(directory.glob(pattern))


def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Get comprehensive file information.
    
    Args:
        file_path: File path
        
    Returns:
        Dictionary with file information
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    stat = file_path.stat()
    
    return {
        "path": str(file_path),
        "name": file_path.name,
        "stem": file_path.stem,
        "suffix": file_path.suffix,
        "size_bytes": stat.st_size,
        "size_kb": stat.st_size / 1024,
        "size_mb": stat.st_size / (1024 * 1024),
        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "is_file": file_path.is_file(),
        "is_dir": file_path.is_dir(),
        "parent": str(file_path.parent),
        "absolute": str(file_path.absolute())
    }


def cleanup_old_files(directory: Union[str, Path], max_age_days: int, pattern: str = "*") -> int:
    """
    Clean up old files in directory.
    
    Args:
        directory: Directory to clean
        max_age_days: Maximum age in days
        pattern: File pattern to match
        
    Returns:
        Number of files deleted
    """
    directory = Path(directory)
    
    if not directory.exists():
        return 0
    
    cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)
    deleted_count = 0
    
    for file_path in directory.glob(pattern):
        if file_path.is_file():
            try:
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted old file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete {file_path}: {e}")
    
    return deleted_count


def archive_directory(source_dir: Union[str, Path], archive_path: Union[str, Path], format: str = 'zip') -> Path:
    """
    Create archive of directory.
    
    Args:
        source_dir: Source directory to archive
        archive_path: Archive file path (without extension)
        format: Archive format (zip, tar, gztar, bztar, xztar)
        
    Returns:
        Path to created archive
    """
    source_dir = Path(source_dir)
    archive_path = Path(archive_path)
    
    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")
    
    # Ensure archive directory exists
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create archive
    archive_file = shutil.make_archive(
        str(archive_path),
        format,
        str(source_dir.parent),
        str(source_dir.name)
    )
    
    logger.info(f"Created archive: {archive_file}")
    return Path(archive_file)


class FileManager:
    """
    File manager with context management and automatic cleanup.
    """
    
    def __init__(self, base_dir: Union[str, Path]):
        """
        Initialize file manager.
        
        Args:
            base_dir: Base directory for operations
        """
        self.base_dir = Path(base_dir)
        self.temp_files: List[Path] = []
        self.logger = get_logger(self.__class__.__name__)
    
    def create_temp_file(self, suffix: str = '.tmp', content: Optional[str] = None) -> Path:
        """
        Create temporary file.
        
        Args:
            suffix: File suffix
            content: Optional initial content
            
        Returns:
            Path to temporary file
        """
        import tempfile
        
        temp_file = Path(tempfile.mktemp(suffix=suffix, dir=self.base_dir))
        self.temp_files.append(temp_file)
        
        if content is not None:
            safe_file_write(temp_file, content)
        
        self.logger.debug(f"Created temp file: {temp_file}")
        return temp_file
    
    def cleanup_temp_files(self) -> None:
        """Clean up all temporary files."""
        for temp_file in self.temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
                    self.logger.debug(f"Cleaned up temp file: {temp_file}")
            except Exception as e:
                self.logger.warning(f"Failed to cleanup {temp_file}: {e}")
        
        self.temp_files.clear()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup_temp_files()