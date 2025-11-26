"""
Filesystem tool for safe file operations.
"""
import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from core.interfaces import Tool
from core.config import settings
from core.logging_config import log
from core.utils import (
    safe_read_file, get_file_info, sanitize_filename, 
    is_text_file, is_git_ignored, parse_gitignore
)


class FilesystemTool(Tool):
    """Tool for safe filesystem operations."""
    
    def __init__(self):
        self.base_path = Path(settings.project_root).resolve()
        self.exclude_patterns = [
            '.git', '__pycache__', 'node_modules', '.vscode', 
            '.idea', 'venv', 'env', '.env', 'dist', 'build'
        ]
        # Add gitignore patterns if available
        gitignore_patterns = parse_gitignore(self.base_path)
        self.exclude_patterns.extend(gitignore_patterns)
    
    async def execute(self, operation: str, **kwargs) -> Any:
        """Execute filesystem operation."""
        try:
            if operation == "read_file":
                return await self.read_file(kwargs.get("path"))
            elif operation == "write_file":
                return await self.write_file(
                    kwargs.get("path"), 
                    kwargs.get("content"),
                    kwargs.get("create_dirs", True)
                )
            elif operation == "list_files":
                return await self.list_files(
                    kwargs.get("directory", "."),
                    kwargs.get("pattern", "*"),
                    kwargs.get("recursive", False)
                )
            elif operation == "file_info":
                return await self.file_info(kwargs.get("path"))
            elif operation == "delete_file":
                return await self.delete_file(kwargs.get("path"))
            elif operation == "create_directory":
                return await self.create_directory(kwargs.get("path"))
            elif operation == "copy_file":
                return await self.copy_file(
                    kwargs.get("source"),
                    kwargs.get("destination")
                )
            elif operation == "move_file":
                return await self.move_file(
                    kwargs.get("source"),
                    kwargs.get("destination")
                )
            elif operation == "search_in_files":
                return await self.search_in_files(
                    kwargs.get("pattern"),
                    kwargs.get("directory", "."),
                    kwargs.get("file_pattern", "*")
                )
            else:
                raise ValueError(f"Unknown operation: {operation}")
                
        except Exception as e:
            log.error(f"Filesystem tool error: {str(e)}")
            return {"error": str(e)}
    
    async def read_file(self, path: str) -> Dict[str, Any]:
        """Read file content safely."""
        try:
            file_path = self._resolve_path(path)
            if not file_path.exists():
                return {"error": f"File not found: {path}"}
            
            if not file_path.is_file():
                return {"error": f"Path is not a file: {path}"}
            
            if not self._is_allowed_path(file_path):
                return {"error": f"Access denied: {path}"}
            
            content = safe_read_file(file_path)
            if content is None:
                return {"error": f"Cannot read file (too large or binary): {path}"}
            
            info = get_file_info(file_path)
            
            return {
                "content": content,
                "info": info,
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def write_file(self, path: str, content: str, create_dirs: bool = True) -> Dict[str, Any]:
        """Write content to file safely."""
        try:
            file_path = self._resolve_path(path)
            
            if not self._is_allowed_path(file_path):
                return {"error": f"Access denied: {path}"}
            
            # Create directories if needed
            if create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            info = get_file_info(file_path)
            
            return {
                "message": f"File written successfully: {path}",
                "info": info,
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def list_files(self, directory: str = ".", pattern: str = "*", 
                        recursive: bool = False) -> Dict[str, Any]:
        """List files in directory."""
        try:
            dir_path = self._resolve_path(directory)
            if not dir_path.exists():
                return {"error": f"Directory not found: {directory}"}
            
            if not dir_path.is_dir():
                return {"error": f"Path is not a directory: {directory}"}
            
            if not self._is_allowed_path(dir_path):
                return {"error": f"Access denied: {directory}"}
            
            files = []
            
            if recursive:
                pattern_path = f"**/{pattern}"
                file_paths = dir_path.glob(pattern_path)
            else:
                file_paths = dir_path.glob(pattern)
            
            for file_path in file_paths:
                if file_path.is_file() and self._is_allowed_path(file_path):
                    if not is_git_ignored(file_path, self.base_path):
                        info = get_file_info(file_path)
                        files.append(info)
            
            # Sort by name
            files.sort(key=lambda x: x['name'])
            
            return {
                "files": files,
                "directory": str(dir_path),
                "count": len(files),
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def file_info(self, path: str) -> Dict[str, Any]:
        """Get file information."""
        try:
            file_path = self._resolve_path(path)
            if not file_path.exists():
                return {"error": f"File not found: {path}"}
            
            if not self._is_allowed_path(file_path):
                return {"error": f"Access denied: {path}"}
            
            info = get_file_info(file_path)
            return {"info": info, "success": True}
            
        except Exception as e:
            return {"error": str(e)}
    
    async def delete_file(self, path: str) -> Dict[str, Any]:
        """Delete file safely."""
        try:
            file_path = self._resolve_path(path)
            if not file_path.exists():
                return {"error": f"File not found: {path}"}
            
            if not self._is_allowed_path(file_path):
                return {"error": f"Access denied: {path}"}
            
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                shutil.rmtree(file_path)
            
            return {
                "message": f"Deleted successfully: {path}",
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def create_directory(self, path: str) -> Dict[str, Any]:
        """Create directory."""
        try:
            dir_path = self._resolve_path(path)
            
            if not self._is_allowed_path(dir_path):
                return {"error": f"Access denied: {path}"}
            
            dir_path.mkdir(parents=True, exist_ok=True)
            
            return {
                "message": f"Directory created successfully: {path}",
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def copy_file(self, source: str, destination: str) -> Dict[str, Any]:
        """Copy file safely."""
        try:
            source_path = self._resolve_path(source)
            dest_path = self._resolve_path(destination)
            
            if not self._is_allowed_path(source_path) or not self._is_allowed_path(dest_path):
                return {"error": f"Access denied"}
            
            if not source_path.exists():
                return {"error": f"Source file not found: {source}"}
            
            # Create destination directory if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            if source_path.is_file():
                shutil.copy2(source_path, dest_path)
            elif source_path.is_dir():
                shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
            
            return {
                "message": f"Copied successfully from {source} to {destination}",
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def move_file(self, source: str, destination: str) -> Dict[str, Any]:
        """Move file safely."""
        try:
            source_path = self._resolve_path(source)
            dest_path = self._resolve_path(destination)
            
            if not self._is_allowed_path(source_path) or not self._is_allowed_path(dest_path):
                return {"error": f"Access denied"}
            
            if not source_path.exists():
                return {"error": f"Source file not found: {source}"}
            
            # Create destination directory if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(source_path), str(dest_path))
            
            return {
                "message": f"Moved successfully from {source} to {destination}",
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def search_in_files(self, pattern: str, directory: str = ".", 
                             file_pattern: str = "*") -> Dict[str, Any]:
        """Search for pattern in files."""
        try:
            import re
            
            dir_path = self._resolve_path(directory)
            if not dir_path.exists():
                return {"error": f"Directory not found: {directory}"}
            
            if not self._is_allowed_path(dir_path):
                return {"error": f"Access denied: {directory}"}
            
            regex = re.compile(pattern, re.IGNORECASE)
            matches = []
            
            for file_path in dir_path.rglob(file_pattern):
                if (file_path.is_file() and 
                    self._is_allowed_path(file_path) and 
                    is_text_file(file_path) and
                    not is_git_ignored(file_path, self.base_path)):
                    
                    content = safe_read_file(file_path, max_size=1024*1024)  # 1MB limit
                    if content:
                        lines = content.split('\n')
                        for line_num, line in enumerate(lines, 1):
                            if regex.search(line):
                                matches.append({
                                    'file': str(file_path.relative_to(self.base_path)),
                                    'line_number': line_num,
                                    'line_content': line.strip(),
                                    'match': regex.search(line).group()
                                })
            
            return {
                "matches": matches,
                "pattern": pattern,
                "directory": directory,
                "count": len(matches),
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve path relative to base path."""
        return (self.base_path / path).resolve()
    
    def _is_allowed_path(self, path: Path) -> bool:
        """Check if path is allowed for access."""
        try:
            # Check if path is within base path
            path.resolve().relative_to(self.base_path)
            
            # Check exclude patterns
            for pattern in self.exclude_patterns:
                if path.match(pattern) or any(parent.match(pattern) for parent in path.parents):
                    return False
            
            return True
        except ValueError:
            return False
    
    def description(self) -> str:
        """Get tool description."""
        return "Safe filesystem operations including read, write, list, search, and file management"
    
    def parameters(self) -> Dict[str, Any]:
        """Get tool parameter schema."""
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": [
                        "read_file", "write_file", "list_files", "file_info",
                        "delete_file", "create_directory", "copy_file", "move_file",
                        "search_in_files"
                    ]
                },
                "path": {"type": "string"},
                "content": {"type": "string"},
                "directory": {"type": "string"},
                "pattern": {"type": "string"},
                "recursive": {"type": "boolean"},
                "source": {"type": "string"},
                "destination": {"type": "string"},
                "create_dirs": {"type": "boolean"}
            },
            "required": ["operation"]
        }