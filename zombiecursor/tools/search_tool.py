"""
Search tool for finding information in code and documentation.
"""
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from core.interfaces import Tool
from core.config import settings
from core.logging_config import log
from core.utils import (
    find_files_by_pattern, safe_read_file, is_text_file,
    is_git_ignored, parse_gitignore, extract_code_blocks
)


class SearchTool(Tool):
    """Tool for searching in code and documentation."""
    
    def __init__(self):
        self.base_path = Path(settings.project_root).resolve()
        self.exclude_patterns = [
            '.git', '__pycache__', 'node_modules', '.vscode', 
            '.idea', 'venv', 'env', '.env', 'dist', 'build'
        ]
        gitignore_patterns = parse_gitignore(self.base_path)
        self.exclude_patterns.extend(gitignore_patterns)
    
    async def execute(self, operation: str, **kwargs) -> Any:
        """Execute search operation."""
        try:
            if operation == "search_text":
                return await self.search_text(
                    kwargs.get("query"),
                    kwargs.get("directory", "."),
                    kwargs.get("file_patterns", ["*"]),
                    kwargs.get("case_sensitive", False),
                    kwargs.get("regex", False),
                    kwargs.get("max_results", 100)
                )
            elif operation == "search_files":
                return await self.search_files(
                    kwargs.get("patterns", ["*"]),
                    kwargs.get("directory", "."),
                    kwargs.get("exclude_patterns", []),
                    kwargs.get("max_results", 100)
                )
            elif operation == "search_functions":
                return await self.search_functions(
                    kwargs.get("function_name"),
                    kwargs.get("directory", "."),
                    kwargs.get("file_patterns", ["*.py"]),
                    kwargs.get("exact_match", False)
                )
            elif operation == "search_classes":
                return await self.search_classes(
                    kwargs.get("class_name"),
                    kwargs.get("directory", "."),
                    kwargs.get("file_patterns", ["*.py"]),
                    kwargs.get("exact_match", False)
                )
            elif operation == "search_imports":
                return await self.search_imports(
                    kwargs.get("module_name"),
                    kwargs.get("directory", "."),
                    kwargs.get("file_patterns", ["*.py"])
                )
            elif operation == "search_documentation":
                return await self.search_documentation(
                    kwargs.get("query"),
                    kwargs.get("directory", "."),
                    kwargs.get("file_patterns", ["*.md", "*.rst", "*.txt"])
                )
            elif operation == "find_references":
                return await self.find_references(
                    kwargs.get("symbol"),
                    kwargs.get("directory", "."),
                    kwargs.get("file_patterns", ["*.py"])
                )
            else:
                raise ValueError(f"Unknown operation: {operation}")
                
        except Exception as e:
            log.error(f"Search tool error: {str(e)}")
            return {"error": str(e)}
    
    async def search_text(self, query: str, directory: str = ".", 
                         file_patterns: List[str] = None,
                         case_sensitive: bool = False, 
                         regex: bool = False,
                         max_results: int = 100) -> Dict[str, Any]:
        """Search for text in files."""
        try:
            if not query.strip():
                return {"error": "Empty search query provided"}
            
            if file_patterns is None:
                file_patterns = ["*"]
            
            dir_path = self._resolve_path(directory)
            if not dir_path.exists():
                return {"error": f"Directory not found: {directory}"}
            
            # Prepare search pattern
            if regex:
                try:
                    pattern = re.compile(query, 0 if case_sensitive else re.IGNORECASE)
                except re.error as e:
                    return {"error": f"Invalid regex pattern: {str(e)}"}
            else:
                pattern = re.compile(
                    re.escape(query), 
                    0 if case_sensitive else re.IGNORECASE
                )
            
            matches = []
            files_searched = 0
            
            for file_pattern in file_patterns:
                files = find_files_by_pattern(dir_path, [file_pattern], self.exclude_patterns)
                
                for file_path in files:
                    if (is_text_file(file_path) and 
                        not is_git_ignored(file_path, self.base_path)):
                        
                        files_searched += 1
                        content = safe_read_file(file_path, max_size=1024*1024)  # 1MB limit
                        
                        if content:
                            lines = content.split('\n')
                            for line_num, line in enumerate(lines, 1):
                                match = pattern.search(line)
                                if match:
                                    matches.append({
                                        'file': str(file_path.relative_to(self.base_path)),
                                        'line_number': line_num,
                                        'line_content': line.strip(),
                                        'match': match.group(),
                                        'start_pos': match.start(),
                                        'end_pos': match.end()
                                    })
                                    
                                    if len(matches) >= max_results:
                                        break
                    
                    if len(matches) >= max_results:
                        break
                
                if len(matches) >= max_results:
                    break
            
            return {
                "matches": matches,
                "query": query,
                "directory": directory,
                "file_patterns": file_patterns,
                "case_sensitive": case_sensitive,
                "regex": regex,
                "files_searched": files_searched,
                "total_matches": len(matches),
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def search_files(self, patterns: List[str], directory: str = ".",
                          exclude_patterns: List[str] = None,
                          max_results: int = 100) -> Dict[str, Any]:
        """Search for files by pattern."""
        try:
            if not patterns:
                return {"error": "No file patterns provided"}
            
            if exclude_patterns is None:
                exclude_patterns = []
            
            dir_path = self._resolve_path(directory)
            if not dir_path.exists():
                return {"error": f"Directory not found: {directory}"}
            
            all_exclude = self.exclude_patterns + exclude_patterns
            files = find_files_by_pattern(dir_path, patterns, all_exclude)
            
            # Filter and limit results
            result_files = []
            for file_path in files[:max_results]:
                if (is_text_file(file_path) and 
                    not is_git_ignored(file_path, self.base_path)):
                    
                    result_files.append({
                        'path': str(file_path.relative_to(self.base_path)),
                        'name': file_path.name,
                        'size': file_path.stat().st_size,
                        'extension': file_path.suffix
                    })
            
            return {
                "files": result_files,
                "patterns": patterns,
                "directory": directory,
                "total_found": len(result_files),
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def search_functions(self, function_name: str, directory: str = ".",
                              file_patterns: List[str] = None,
                              exact_match: bool = False) -> Dict[str, Any]:
        """Search for function definitions."""
        try:
            if not function_name.strip():
                return {"error": "Empty function name provided"}
            
            if file_patterns is None:
                file_patterns = ["*.py"]
            
            dir_path = self._resolve_path(directory)
            if not dir_path.exists():
                return {"error": f"Directory not found: {directory}"}
            
            # Prepare function pattern
            if exact_match:
                pattern = re.compile(rf'def\s+{re.escape(function_name)}\s*\(')
            else:
                pattern = re.compile(rf'def\s+.*{re.escape(function_name)}.*\s*\(')
            
            matches = []
            
            for file_pattern in file_patterns:
                files = find_files_by_pattern(dir_path, [file_pattern], self.exclude_patterns)
                
                for file_path in files:
                    if (file_path.suffix == '.py' and 
                        is_text_file(file_path) and
                        not is_git_ignored(file_path, self.base_path)):
                        
                        content = safe_read_file(file_path)
                        if content:
                            lines = content.split('\n')
                            for line_num, line in enumerate(lines, 1):
                                match = pattern.search(line)
                                if match:
                                    # Try to extract function signature
                                    signature = line.strip()
                                    if not signature.endswith(':'):
                                        # Look for the rest of the signature
                                        for i in range(line_num, min(line_num + 3, len(lines))):
                                            if lines[i].strip().endswith(':'):
                                                signature += ' ' + lines[i].strip()
                                                break
                                    
                                    matches.append({
                                        'file': str(file_path.relative_to(self.base_path)),
                                        'line_number': line_num,
                                        'function_name': function_name,
                                        'signature': signature,
                                        'line_content': line.strip()
                                    })
            
            return {
                "matches": matches,
                "function_name": function_name,
                "directory": directory,
                "exact_match": exact_match,
                "total_found": len(matches),
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def search_classes(self, class_name: str, directory: str = ".",
                           file_patterns: List[str] = None,
                           exact_match: bool = False) -> Dict[str, Any]:
        """Search for class definitions."""
        try:
            if not class_name.strip():
                return {"error": "Empty class name provided"}
            
            if file_patterns is None:
                file_patterns = ["*.py"]
            
            dir_path = self._resolve_path(directory)
            if not dir_path.exists():
                return {"error": f"Directory not found: {directory}"}
            
            # Prepare class pattern
            if exact_match:
                pattern = re.compile(rf'class\s+{re.escape(class_name)}\s*[\(:]')
            else:
                pattern = re.compile(rf'class\s+.*{re.escape(class_name)}.*\s*[\(:]')
            
            matches = []
            
            for file_pattern in file_patterns:
                files = find_files_by_pattern(dir_path, [file_pattern], self.exclude_patterns)
                
                for file_path in files:
                    if (file_path.suffix == '.py' and 
                        is_text_file(file_path) and
                        not is_git_ignored(file_path, self.base_path)):
                        
                        content = safe_read_file(file_path)
                        if content:
                            lines = content.split('\n')
                            for line_num, line in enumerate(lines, 1):
                                match = pattern.search(line)
                                if match:
                                    matches.append({
                                        'file': str(file_path.relative_to(self.base_path)),
                                        'line_number': line_num,
                                        'class_name': class_name,
                                        'line_content': line.strip()
                                    })
            
            return {
                "matches": matches,
                "class_name": class_name,
                "directory": directory,
                "exact_match": exact_match,
                "total_found": len(matches),
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def search_imports(self, module_name: str, directory: str = ".",
                           file_patterns: List[str] = None) -> Dict[str, Any]:
        """Search for import statements."""
        try:
            if not module_name.strip():
                return {"error": "Empty module name provided"}
            
            if file_patterns is None:
                file_patterns = ["*.py"]
            
            dir_path = self._resolve_path(directory)
            if not dir_path.exists():
                return {"error": f"Directory not found: {directory}"}
            
            # Prepare import patterns
            patterns = [
                re.compile(rf'import\s+.*{re.escape(module_name)}.*'),
                re.compile(rf'from\s+.*{re.escape(module_name)}.*\s+import')
            ]
            
            matches = []
            
            for file_pattern in file_patterns:
                files = find_files_by_pattern(dir_path, [file_pattern], self.exclude_patterns)
                
                for file_path in files:
                    if (file_path.suffix == '.py' and 
                        is_text_file(file_path) and
                        not is_git_ignored(file_path, self.base_path)):
                        
                        content = safe_read_file(file_path)
                        if content:
                            lines = content.split('\n')
                            for line_num, line in enumerate(lines, 1):
                                line_stripped = line.strip()
                                for pattern in patterns:
                                    match = pattern.search(line_stripped)
                                    if match:
                                        matches.append({
                                            'file': str(file_path.relative_to(self.base_path)),
                                            'line_number': line_num,
                                            'import_statement': line_stripped,
                                            'module_name': module_name
                                        })
                                        break
            
            return {
                "matches": matches,
                "module_name": module_name,
                "directory": directory,
                "total_found": len(matches),
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def search_documentation(self, query: str, directory: str = ".",
                                 file_patterns: List[str] = None) -> Dict[str, Any]:
        """Search in documentation files."""
        try:
            if not query.strip():
                return {"error": "Empty search query provided"}
            
            if file_patterns is None:
                file_patterns = ["*.md", "*.rst", "*.txt"]
            
            dir_path = self._resolve_path(directory)
            if not dir_path.exists():
                return {"error": f"Directory not found: {directory}"}
            
            # Prepare search pattern
            pattern = re.compile(re.escape(query), re.IGNORECASE)
            
            matches = []
            
            for file_pattern in file_patterns:
                files = find_files_by_pattern(dir_path, [file_pattern], self.exclude_patterns)
                
                for file_path in files:
                    if (is_text_file(file_path) and 
                        not is_git_ignored(file_path, self.base_path)):
                        
                        content = safe_read_file(file_path)
                        if content:
                            lines = content.split('\n')
                            for line_num, line in enumerate(lines, 1):
                                match = pattern.search(line)
                                if match:
                                    matches.append({
                                        'file': str(file_path.relative_to(self.base_path)),
                                        'line_number': line_num,
                                        'line_content': line.strip(),
                                        'match': match.group()
                                    })
            
            return {
                "matches": matches,
                "query": query,
                "directory": directory,
                "file_patterns": file_patterns,
                "total_found": len(matches),
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def find_references(self, symbol: str, directory: str = ".",
                            file_patterns: List[str] = None) -> Dict[str, Any]:
        """Find references to a symbol."""
        try:
            if not symbol.strip():
                return {"error": "Empty symbol provided"}
            
            if file_patterns is None:
                file_patterns = ["*.py"]
            
            dir_path = self._resolve_path(directory)
            if not dir_path.exists():
                return {"error": f"Directory not found: {directory}"}
            
            # Simple reference finding - look for symbol usage
            pattern = re.compile(rf'\b{re.escape(symbol)}\b')
            
            matches = []
            
            for file_pattern in file_patterns:
                files = find_files_by_pattern(dir_path, [file_pattern], self.exclude_patterns)
                
                for file_path in files:
                    if (file_path.suffix == '.py' and 
                        is_text_file(file_path) and
                        not is_git_ignored(file_path, self.base_path)):
                        
                        content = safe_read_file(file_path)
                        if content:
                            lines = content.split('\n')
                            for line_num, line in enumerate(lines, 1):
                                match = pattern.search(line)
                                if match:
                                    # Try to determine context
                                    context = "unknown"
                                    line_stripped = line.strip()
                                    if 'def ' in line_stripped:
                                        context = "function_definition"
                                    elif 'class ' in line_stripped:
                                        context = "class_definition"
                                    elif 'import ' in line_stripped or 'from ' in line_stripped:
                                        context = "import"
                                    elif f'{symbol}(' in line_stripped:
                                        context = "function_call"
                                    elif f'{symbol}.' in line_stripped:
                                        context = "attribute_access"
                                    elif f' {symbol} ' in line_stripped or f' {symbol}=' in line_stripped:
                                        context = "variable_usage"
                                    
                                    matches.append({
                                        'file': str(file_path.relative_to(self.base_path)),
                                        'line_number': line_num,
                                        'line_content': line.strip(),
                                        'context': context,
                                        'symbol': symbol
                                    })
            
            return {
                "matches": matches,
                "symbol": symbol,
                "directory": directory,
                "total_found": len(matches),
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve path relative to base path."""
        return (self.base_path / path).resolve()
    
    def description(self) -> str:
        """Get tool description."""
        return "Search tool for finding text, functions, classes, imports, and references in code"
    
    def parameters(self) -> Dict[str, Any]:
        """Get tool parameter schema."""
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": [
                        "search_text", "search_files", "search_functions",
                        "search_classes", "search_imports", "search_documentation",
                        "find_references"
                    ]
                },
                "query": {"type": "string"},
                "patterns": {"type": "array", "items": {"type": "string"}},
                "directory": {"type": "string"},
                "file_patterns": {"type": "array", "items": {"type": "string"}},
                "exclude_patterns": {"type": "array", "items": {"type": "string"}},
                "case_sensitive": {"type": "boolean"},
                "regex": {"type": "boolean"},
                "max_results": {"type": "integer"},
                "exact_match": {"type": "boolean"},
                "function_name": {"type": "string"},
                "class_name": {"type": "string"},
                "module_name": {"type": "string"},
                "symbol": {"type": "string"}
            },
            "required": ["operation"]
        }