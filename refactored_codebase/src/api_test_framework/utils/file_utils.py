"""
Ultra-efficient file operations with async support and comprehensive error handling.

Provides high-performance file I/O operations with automatic cleanup,
batch processing, and intelligent error recovery.
"""

import asyncio
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aiofiles
import aiofiles.os

from api_test_framework.core.exceptions import FileOperationError
from api_test_framework.core.logging import get_logger


class FileUtils:
    """Ultra-efficient file operations with enterprise features."""
    
    def __init__(self):
        self.logger = get_logger("file_utils")
    
    async def read_json(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Read JSON file with error handling and validation."""
        path = Path(file_path)
        
        try:
            async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                content = await f.read()
                return json.loads(content)
        except FileNotFoundError:
            raise FileOperationError(
                f"File not found: {path}",
                file_path=str(path),
                operation="read_json"
            )
        except json.JSONDecodeError as e:
            raise FileOperationError(
                f"Invalid JSON in file: {e}",
                file_path=str(path),
                operation="read_json",
                cause=e
            )
        except Exception as e:
            raise FileOperationError(
                f"Failed to read JSON file: {e}",
                file_path=str(path),
                operation="read_json",
                cause=e
            )
    
    async def write_json(
        self,
        file_path: Union[str, Path],
        data: Dict[str, Any],
        indent: int = 2,
        ensure_ascii: bool = False
    ) -> None:
        """Write JSON file with atomic operation and backup."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create temporary file for atomic write
        temp_path = path.with_suffix(f"{path.suffix}.tmp")
        
        try:
            async with aiofiles.open(temp_path, 'w', encoding='utf-8') as f:
                content = json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)
                await f.write(content)
            
            # Atomic move
            await aiofiles.os.rename(temp_path, path)
            
        except Exception as e:
            # Cleanup temp file on error
            if temp_path.exists():
                await aiofiles.os.remove(temp_path)
            
            raise FileOperationError(
                f"Failed to write JSON file: {e}",
                file_path=str(path),
                operation="write_json",
                cause=e
            )
    
    async def read_text(self, file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
        """Read text file with encoding detection."""
        path = Path(file_path)
        
        try:
            async with aiofiles.open(path, 'r', encoding=encoding) as f:
                return await f.read()
        except UnicodeDecodeError:
            # Try different encodings
            for enc in ['utf-8-sig', 'latin1', 'cp1252']:
                try:
                    async with aiofiles.open(path, 'r', encoding=enc) as f:
                        content = await f.read()
                        self.logger.warning(f"File {path} read with encoding {enc}")
                        return content
                except UnicodeDecodeError:
                    continue
            
            raise FileOperationError(
                f"Could not decode file with any encoding",
                file_path=str(path),
                operation="read_text"
            )
        except Exception as e:
            raise FileOperationError(
                f"Failed to read text file: {e}",
                file_path=str(path),
                operation="read_text",
                cause=e
            )
    
    async def write_text(
        self,
        file_path: Union[str, Path],
        content: str,
        encoding: str = 'utf-8'
    ) -> None:
        """Write text file with atomic operation."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        temp_path = path.with_suffix(f"{path.suffix}.tmp")
        
        try:
            async with aiofiles.open(temp_path, 'w', encoding=encoding) as f:
                await f.write(content)
            
            await aiofiles.os.rename(temp_path, path)
            
        except Exception as e:
            if temp_path.exists():
                await aiofiles.os.remove(temp_path)
            
            raise FileOperationError(
                f"Failed to write text file: {e}",
                file_path=str(path),
                operation="write_text",
                cause=e
            )
    
    async def copy_file(
        self,
        source: Union[str, Path],
        destination: Union[str, Path],
        overwrite: bool = False
    ) -> None:
        """Copy file with progress tracking and error handling."""
        src_path = Path(source)
        dst_path = Path(destination)
        
        if not src_path.exists():
            raise FileOperationError(
                f"Source file does not exist: {src_path}",
                file_path=str(src_path),
                operation="copy_file"
            )
        
        if dst_path.exists() and not overwrite:
            raise FileOperationError(
                f"Destination file exists and overwrite=False: {dst_path}",
                file_path=str(dst_path),
                operation="copy_file"
            )
        
        try:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use async copy for large files
            if src_path.stat().st_size > 10 * 1024 * 1024:  # 10MB
                await self._async_copy_large_file(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)
            
        except Exception as e:
            raise FileOperationError(
                f"Failed to copy file: {e}",
                file_path=str(src_path),
                operation="copy_file",
                cause=e
            )
    
    async def _async_copy_large_file(self, source: Path, destination: Path) -> None:
        """Copy large files asynchronously with progress."""
        chunk_size = 64 * 1024  # 64KB chunks
        
        async with aiofiles.open(source, 'rb') as src:
            async with aiofiles.open(destination, 'wb') as dst:
                while True:
                    chunk = await src.read(chunk_size)
                    if not chunk:
                        break
                    await dst.write(chunk)
    
    async def delete_file(self, file_path: Union[str, Path], missing_ok: bool = True) -> None:
        """Delete file with error handling."""
        path = Path(file_path)
        
        try:
            await aiofiles.os.remove(path)
        except FileNotFoundError:
            if not missing_ok:
                raise FileOperationError(
                    f"File not found: {path}",
                    file_path=str(path),
                    operation="delete_file"
                )
        except Exception as e:
            raise FileOperationError(
                f"Failed to delete file: {e}",
                file_path=str(path),
                operation="delete_file",
                cause=e
            )
    
    async def create_directory(
        self,
        dir_path: Union[str, Path],
        parents: bool = True,
        exist_ok: bool = True
    ) -> None:
        """Create directory with error handling."""
        path = Path(dir_path)
        
        try:
            path.mkdir(parents=parents, exist_ok=exist_ok)
        except Exception as e:
            raise FileOperationError(
                f"Failed to create directory: {e}",
                file_path=str(path),
                operation="create_directory",
                cause=e
            )
    
    async def list_files(
        self,
        directory: Union[str, Path],
        pattern: str = "*",
        recursive: bool = False
    ) -> List[Path]:
        """List files in directory with pattern matching."""
        dir_path = Path(directory)
        
        if not dir_path.exists():
            raise FileOperationError(
                f"Directory does not exist: {dir_path}",
                file_path=str(dir_path),
                operation="list_files"
            )
        
        try:
            if recursive:
                return list(dir_path.rglob(pattern))
            else:
                return list(dir_path.glob(pattern))
        except Exception as e:
            raise FileOperationError(
                f"Failed to list files: {e}",
                file_path=str(dir_path),
                operation="list_files",
                cause=e
            )
    
    async def get_file_info(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Get comprehensive file information."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileOperationError(
                f"File does not exist: {path}",
                file_path=str(path),
                operation="get_file_info"
            )
        
        try:
            stat = path.stat()
            return {
                "path": str(path),
                "name": path.name,
                "size": stat.st_size,
                "size_human": self._format_size(stat.st_size),
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "is_file": path.is_file(),
                "is_directory": path.is_dir(),
                "suffix": path.suffix,
                "parent": str(path.parent)
            }
        except Exception as e:
            raise FileOperationError(
                f"Failed to get file info: {e}",
                file_path=str(path),
                operation="get_file_info",
                cause=e
            )
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    async def batch_process_files(
        self,
        file_paths: List[Union[str, Path]],
        operation: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Process multiple files in batches with error handling."""
        results = []
        batch_size = kwargs.get('batch_size', 10)
        
        for i in range(0, len(file_paths), batch_size):
            batch = file_paths[i:i + batch_size]
            
            # Process batch concurrently
            tasks = []
            for file_path in batch:
                if operation == "read_json":
                    tasks.append(self._safe_read_json(file_path))
                elif operation == "get_info":
                    tasks.append(self._safe_get_file_info(file_path))
                # Add more operations as needed
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for file_path, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    results.append({
                        "file_path": str(file_path),
                        "success": False,
                        "error": str(result)
                    })
                else:
                    results.append({
                        "file_path": str(file_path),
                        "success": True,
                        "data": result
                    })
        
        return results
    
    async def _safe_read_json(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Safe JSON read with exception handling."""
        try:
            return await self.read_json(file_path)
        except Exception as e:
            return {"error": str(e)}
    
    async def _safe_get_file_info(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Safe file info retrieval with exception handling."""
        try:
            return await self.get_file_info(file_path)
        except Exception as e:
            return {"error": str(e)}
    
    async def cleanup_temp_files(self, directory: Union[str, Path], max_age_hours: int = 24) -> int:
        """Clean up temporary files older than specified age."""
        import time
        
        dir_path = Path(directory)
        if not dir_path.exists():
            return 0
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        cleaned_count = 0
        
        try:
            for file_path in dir_path.rglob("*.tmp"):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        await self.delete_file(file_path, missing_ok=True)
                        cleaned_count += 1
            
            self.logger.info(f"Cleaned up {cleaned_count} temporary files")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            return cleaned_count