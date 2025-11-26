"""
Project context loader for ZombieCursor agents.
"""
import os
import glob
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from core.config import settings
from core.logging_config import log
from core.utils import (
    is_text_file, is_git_ignored, parse_gitignore, 
    get_file_info, get_project_languages, find_files_by_pattern
)


class ProjectContext:
    """Loads and manages project context for agents."""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or settings.project_root).resolve()
        self.max_files = settings.max_context_files
        self.max_size = settings.max_context_size
        
        # Cache for performance
        self._cache = {}
        self._cache_timestamp = None
        
        # Exclude patterns
        self.exclude_patterns = [
            '.git', '__pycache__', 'node_modules', '.vscode', 
            '.idea', 'venv', 'env', '.env', 'dist', 'build',
            '.pytest_cache', '.coverage', 'htmlcov', 'site',
            '.tox', 'coverage.xml', '*.egg-info'
        ]
        
        # Add gitignore patterns
        gitignore_patterns = parse_gitignore(self.base_path)
        self.exclude_patterns.extend(gitignore_patterns)
        
        log.info(f"ProjectContext initialized for: {self.base_path}")
    
    def collect(self, force_refresh: bool = False) -> str:
        """Collect project context as a formatted string."""
        try:
            # Check cache
            if not force_refresh and self._is_cache_valid():
                return self._cache.get('context', '')
            
            context_parts = []
            
            # Add project overview
            overview = self._get_project_overview()
            if overview:
                context_parts.append(overview)
            
            # Add file structure
            file_structure = self._get_file_structure()
            if file_structure:
                context_parts.append(file_structure)
            
            # Add important files content
            important_files = self._get_important_files_content()
            if important_files:
                context_parts.append(important_files)
            
            # Combine all parts
            full_context = '\n\n'.join(context_parts)
            
            # Truncate if too large
            if len(full_context) > self.max_size:
                full_context = full_context[:self.max_size] + "\n...[truncated]"
            
            # Update cache
            self._cache = {
                'context': full_context,
                'timestamp': self._get_current_timestamp()
            }
            
            log.debug(f"Collected project context: {len(full_context)} characters")
            return full_context
            
        except Exception as e:
            log.error(f"Error collecting project context: {str(e)}")
            return f"Error collecting project context: {str(e)}"
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if not self._cache or 'timestamp' not in self._cache:
            return False
        
        # Cache is valid for 5 minutes
        cache_age = self._get_current_timestamp() - self._cache['timestamp']
        return cache_age < 300  # 5 minutes
    
    def _get_current_timestamp(self) -> float:
        """Get current timestamp."""
        import time
        return time.time()
    
    def _get_project_overview(self) -> str:
        """Get project overview information."""
        try:
            overview_parts = []
            
            # Basic info
            overview_parts.append(f"Project Root: {self.base_path}")
            
            # Languages
            languages = get_project_languages(self.base_path)
            if languages:
                lang_list = ', '.join([f"{lang} ({count})" for lang, count in languages.items()])
                overview_parts.append(f"Languages: {lang_list}")
            
            # Git info
            if self._is_git_repository():
                overview_parts.append("Git Repository: Yes")
                try:
                    import subprocess
                    result = subprocess.run(
                        ['git', 'branch', '--show-current'],
                        cwd=self.base_path,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        overview_parts.append(f"Current Branch: {result.stdout.strip()}")
                except Exception:
                    pass
            else:
                overview_parts.append("Git Repository: No")
            
            # File counts
            total_files = len(self._get_all_files())
            overview_parts.append(f"Total Files: {total_files}")
            
            return "Project Overview:\n" + "\n".join(f"  {part}" for part in overview_parts)
            
        except Exception as e:
            log.error(f"Error getting project overview: {str(e)}")
            return ""
    
    def _get_file_structure(self) -> str:
        """Get project file structure."""
        try:
            structure = []
            structure.append("File Structure:")
            
            # Get directory tree
            tree_lines = self._build_tree(self.base_path, prefix="")
            structure.extend(tree_lines)
            
            return "\n".join(structure)
            
        except Exception as e:
            log.error(f"Error getting file structure: {str(e)}")
            return ""
    
    def _build_tree(self, path: Path, prefix: str = "", max_depth: int = 3) -> List[str]:
        """Build directory tree representation."""
        try:
            if max_depth <= 0:
                return []
            
            lines = []
            
            try:
                items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            except PermissionError:
                return [f"{prefix}[Permission Denied]"]
            
            for i, item in enumerate(items):
                if self._should_exclude(item):
                    continue
                
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                child_prefix = "    " if is_last else "│   "
                
                if item.is_dir():
                    lines.append(f"{prefix}{current_prefix}{item.name}/")
                    
                    # Recurse into subdirectories
                    if max_depth > 1:
                        child_lines = self._build_tree(
                            item, 
                            prefix + child_prefix, 
                            max_depth - 1
                        )
                        lines.extend(child_lines)
                
                else:
                    lines.append(f"{prefix}{current_prefix}{item.name}")
            
            return lines
            
        except Exception as e:
            log.error(f"Error building tree for {path}: {str(e)}")
            return [f"{prefix}[Error: {str(e)}]"]
    
    def _get_important_files_content(self) -> str:
        """Get content of important files."""
        try:
            important_files = self._find_important_files()
            if not important_files:
                return ""
            
            content_parts = ["Important Files:"]
            
            for file_path in important_files:
                try:
                    file_info = get_file_info(file_path)
                    if file_info.get('is_text') and file_info.get('size', 0) < 10000:  # 10KB limit
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            file_content = f.read()
                        
                        # Truncate very long files
                        if len(file_content) > 2000:
                            file_content = file_content[:2000] + "\n...[truncated]"
                        
                        relative_path = file_path.relative_to(self.base_path)
                        content_parts.append(f"\n# FILE: {relative_path}")
                        content_parts.append(file_content)
                
                except Exception as e:
                    log.debug(f"Error reading file {file_path}: {str(e)}")
                    continue
            
            return "\n".join(content_parts)
            
        except Exception as e:
            log.error(f"Error getting important files content: {str(e)}")
            return ""
    
    def _find_important_files(self) -> List[Path]:
        """Find important files in the project."""
        important_patterns = [
            'README*', 'readme*',
            'requirements.txt', 'pyproject.toml', 'setup.py', 'setup.cfg',
            'package.json', 'tsconfig.json', 'webpack.config.js',
            'Dockerfile', 'docker-compose.yml', 'docker-compose.yaml',
            '.gitignore', '.env.example',
            'main.py', 'app.py', 'index.js', 'index.ts',
            '__init__.py'
        ]
        
        important_files = []
        
        for pattern in important_patterns:
            files = list(self.base_path.glob(pattern))
            for file_path in files:
                if file_path.is_file() and not self._should_exclude(file_path):
                    important_files.append(file_path)
        
        # Limit number of files
        return important_files[:self.max_files // 2]
    
    def _get_all_files(self) -> List[Path]:
        """Get all files in the project."""
        try:
            all_files = []
            
            for file_path in self.base_path.rglob('*'):
                if (file_path.is_file() and 
                    is_text_file(file_path) and 
                    not self._should_exclude(file_path)):
                    all_files.append(file_path)
            
            return all_files
            
        except Exception as e:
            log.error(f"Error getting all files: {str(e)}")
            return []
    
    def _should_exclude(self, path: Path) -> bool:
        """Check if a path should be excluded."""
        try:
            # Check against exclude patterns
            for pattern in self.exclude_patterns:
                if path.match(pattern):
                    return True
                
                # Check parent directories
                for parent in path.parents:
                    if parent.match(pattern):
                        return True
            
            # Check gitignore
            return is_git_ignored(path, self.base_path)
            
        except Exception:
            return False
    
    def _is_git_repository(self) -> bool:
        """Check if the project is a git repository."""
        return (self.base_path / '.git').exists()
    
    def get_file_context(self, file_path: str, include_surrounding: bool = True) -> str:
        """Get context for a specific file."""
        try:
            full_path = self.base_path / file_path
            
            if not full_path.exists():
                return f"File not found: {file_path}"
            
            if not full_path.is_file():
                return f"Path is not a file: {file_path}"
            
            context_parts = [f"File Context for: {file_path}"]
            
            # File info
            file_info = get_file_info(full_path)
            context_parts.append(f"Size: {file_info.get('size', 0)} bytes")
            context_parts.append(f"Modified: {file_info.get('modified', 'Unknown')}")
            
            # File content
            if file_info.get('is_text'):
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Truncate if too large
                if len(content) > 5000:
                    content = content[:5000] + "\n...[truncated]"
                
                context_parts.append(f"\nContent:\n{content}")
            
            # Surrounding files
            if include_surrounding:
                surrounding_files = self._get_surrounding_files(full_path)
                if surrounding_files:
                    context_parts.append(f"\nSurrounding Files:")
                    for rel_path in surrounding_files[:10]:  # Limit to 10 files
                        context_parts.append(f"  - {rel_path}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            log.error(f"Error getting file context for {file_path}: {str(e)}")
            return f"Error getting file context: {str(e)}"
    
    def _get_surrounding_files(self, file_path: Path) -> List[str]:
        """Get files in the same directory and nearby directories."""
        try:
            surrounding_files = []
            
            # Files in same directory
            same_dir = file_path.parent
            for sibling in same_dir.iterdir():
                if (sibling.is_file() and 
                    sibling != file_path and
                    is_text_file(sibling) and
                    not self._should_exclude(sibling)):
                    surrounding_files.append(str(sibling.relative_to(self.base_path)))
            
            # Files in parent directory
            parent_dir = file_path.parent.parent
            if parent_dir != self.base_path:
                for parent_file in parent_dir.iterdir():
                    if (parent_file.is_file() and
                        is_text_file(parent_file) and
                        not self._should_exclude(parent_file)):
                        surrounding_files.append(str(parent_file.relative_to(self.base_path)))
            
            return surrounding_files
            
        except Exception as e:
            log.error(f"Error getting surrounding files: {str(e)}")
            return []
    
    def search_files(self, pattern: str, file_types: List[str] = None) -> List[Dict[str, Any]]:
        """Search for files matching a pattern."""
        try:
            if file_types is None:
                file_types = ['*']
            
            matching_files = []
            
            for file_type in file_types:
                pattern_path = f"**/{pattern}.{file_type.lstrip('*')}"
                files = list(self.base_path.glob(pattern_path))
                
                for file_path in files:
                    if (file_path.is_file() and 
                        is_text_file(file_path) and
                        not self._should_exclude(file_path)):
                        
                        file_info = get_file_info(file_path)
                        matching_files.append(file_info)
            
            return matching_files
            
        except Exception as e:
            log.error(f"Error searching files: {str(e)}")
            return []
    
    def get_language_stats(self) -> Dict[str, Any]:
        """Get language statistics for the project."""
        try:
            languages = get_project_languages(self.base_path)
            
            stats = {
                'languages': languages,
                'total_files': sum(languages.values()),
                'dominant_language': max(languages.items(), key=lambda x: x[1])[0] if languages else None,
                'language_diversity': len(languages)
            }
            
            return stats
            
        except Exception as e:
            log.error(f"Error getting language stats: {str(e)}")
            return {}
    
    def clear_cache(self):
        """Clear the context cache."""
        self._cache = {}
        self._cache_timestamp = None
        log.info("Project context cache cleared")