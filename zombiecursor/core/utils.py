"""
Utility functions for ZombieCursor.
"""
import os
import re
import mimetypes
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import hashlib


def get_file_hash(file_path: Path) -> str:
    """Get SHA256 hash of a file."""
    hash_sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception:
        return ""


def is_text_file(file_path: Path) -> bool:
    """Check if a file is likely a text file."""
    try:
        mimetype, _ = mimetypes.guess_type(str(file_path))
        if mimetype and mimetype.startswith('text/'):
            return True
        
        # Check common text file extensions
        text_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss', '.sass',
            '.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
            '.md', '.txt', '.rst', '.tex', '.log', '.sql', '.sh', '.bat', '.ps1',
            '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.php', '.rb', '.go', '.rs',
            '.swift', '.kt', '.scala', '.r', '.m', '.pl', '.lua', '.vim', '.dockerfile'
        }
        
        return file_path.suffix.lower() in text_extensions
    except Exception:
        return False


def get_file_info(file_path: Path) -> Dict[str, Any]:
    """Get comprehensive file information."""
    try:
        stat = file_path.stat()
        return {
            'path': str(file_path),
            'name': file_path.name,
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'is_text': is_text_file(file_path),
            'extension': file_path.suffix,
            'hash': get_file_hash(file_path)
        }
    except Exception as e:
        return {'path': str(file_path), 'error': str(e)}


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations."""
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)
    # Trim whitespace and dots
    sanitized = sanitized.strip('. ')
    # Ensure it's not empty
    return sanitized or 'unnamed'


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """Truncate text to specified length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def extract_code_blocks(text: str) -> List[Dict[str, str]]:
    """Extract code blocks from markdown text."""
    pattern = r'```(\w+)?\n(.*?)\n```'
    matches = re.findall(pattern, text, re.DOTALL)
    
    blocks = []
    for lang, code in matches:
        blocks.append({
            'language': lang or 'text',
            'code': code.strip()
        })
    
    return blocks


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def get_relative_path(file_path: Path, base_path: Path) -> str:
    """Get relative path from base path."""
    try:
        return str(file_path.relative_to(base_path))
    except ValueError:
        return str(file_path)


def safe_read_file(file_path: Path, max_size: int = 1024 * 1024) -> Optional[str]:
    """Safely read file content with size limit."""
    try:
        if file_path.stat().st_size > max_size:
            return None
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception:
        return None


def find_files_by_pattern(base_path: Path, patterns: List[str], 
                         exclude_patterns: List[str] = None) -> List[Path]:
    """Find files matching patterns."""
    if exclude_patterns is None:
        exclude_patterns = []
    
    files = []
    
    for pattern in patterns:
        for file_path in base_path.glob(pattern):
            if file_path.is_file():
                # Check exclude patterns
                excluded = False
                for exclude_pattern in exclude_patterns:
                    if file_path.match(exclude_pattern):
                        excluded = True
                        break
                
                if not excluded:
                    files.append(file_path)
    
    return sorted(list(set(files)))


def parse_gitignore(base_path: Path) -> List[str]:
    """Parse .gitignore file and return patterns."""
    gitignore_path = base_path / '.gitignore'
    if not gitignore_path.exists():
        return []
    
    patterns = []
    try:
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    patterns.append(line)
    except Exception:
        pass
    
    return patterns


def is_git_ignored(file_path: Path, base_path: Path) -> bool:
    """Check if file is ignored by git."""
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'check-ignore', str(file_path)],
            cwd=base_path,
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False


def get_project_languages(base_path: Path) -> Dict[str, int]:
    """Get language statistics for the project."""
    language_extensions = {
        'Python': ['.py'],
        'JavaScript': ['.js'],
        'TypeScript': ['.ts'],
        'React': ['.jsx'],
        'React TypeScript': ['.tsx'],
        'HTML': ['.html', '.htm'],
        'CSS': ['.css'],
        'SCSS': ['.scss'],
        'Java': ['.java'],
        'C': ['.c'],
        'C++': ['.cpp', '.cxx', '.cc'],
        'C#': ['.cs'],
        'Go': ['.go'],
        'Rust': ['.rs'],
        'PHP': ['.php'],
        'Ruby': ['.rb'],
        'Swift': ['.swift'],
        'Kotlin': ['.kt'],
        'Scala': ['.scala'],
        'R': ['.r'],
        'Shell': ['.sh', '.bash', '.zsh'],
        'PowerShell': ['.ps1'],
        'Docker': ['.dockerfile', 'Dockerfile'],
        'SQL': ['.sql'],
        'Markdown': ['.md'],
        'YAML': ['.yaml', '.yml'],
        'JSON': ['.json'],
        'XML': ['.xml'],
        'TOML': ['.toml'],
        'INI': ['.ini', '.cfg', '.conf'],
    }
    
    language_counts = {lang: 0 for lang in language_extensions}
    
    try:
        for file_path in base_path.rglob('*'):
            if file_path.is_file() and is_text_file(file_path):
                ext = file_path.suffix.lower()
                for lang, extensions in language_extensions.items():
                    if ext in extensions:
                        language_counts[lang] += 1
                        break
    except Exception:
        pass
    
    # Remove languages with zero counts
    return {lang: count for lang, count in language_counts.items() if count > 0}