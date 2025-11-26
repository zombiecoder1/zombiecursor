"""
Git tool for version control operations.
"""
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from core.interfaces import Tool
from core.config import settings
from core.logging_config import log


class GitTool(Tool):
    """Tool for Git version control operations."""
    
    def __init__(self):
        self.base_path = Path(settings.project_root).resolve()
        self.git_path = self._find_git_executable()
    
    def _find_git_executable(self) -> str:
        """Find Git executable."""
        try:
            result = subprocess.run(['git', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                return 'git'
        except FileNotFoundError:
            pass
        
        # Try common Windows paths
        windows_paths = [
            r'C:\Program Files\Git\bin\git.exe',
            r'C:\Program Files (x86)\Git\bin\git.exe',
            r'C:\msys64\usr\bin\git.exe'
        ]
        
        for path in windows_paths:
            if Path(path).exists():
                return path
        
        raise FileNotFoundError("Git executable not found")
    
    async def execute(self, operation: str, **kwargs) -> Any:
        """Execute Git operation."""
        try:
            if not self._is_git_repository():
                return {"error": "Not a Git repository"}
            
            if operation == "status":
                return await self.get_status()
            elif operation == "log":
                return await self.get_log(
                    kwargs.get("max_count", 10),
                    kwargs.get("author"),
                    kwargs.get("since")
                )
            elif operation == "diff":
                return await self.get_diff(
                    kwargs.get("file_path"),
                    kwargs.get("commit1"),
                    kwargs.get("commit2")
                )
            elif operation == "add":
                return await self.add_files(kwargs.get("files", ["."]))
            elif operation == "commit":
                return await self.commit(
                    kwargs.get("message"),
                    kwargs.get("files")
                )
            elif operation == "branch":
                return await self.branch_operations(
                    kwargs.get("action", "list"),
                    kwargs.get("branch_name"),
                    kwargs.get("base_branch")
                )
            elif operation == "checkout":
                return await self.checkout(kwargs.get("target"))
            elif operation == "merge":
                return await self.merge(kwargs.get("branch"))
            elif operation == "pull":
                return await self.pull(kwargs.get("remote", "origin"), kwargs.get("branch"))
            elif operation == "push":
                return await self.push(kwargs.get("remote", "origin"), kwargs.get("branch"))
            elif operation == "stash":
                return await self.stash_operations(
                    kwargs.get("action", "list"),
                    kwargs.get("message")
                )
            elif operation == "reset":
                return await self.reset(
                    kwargs.get("target", "HEAD"),
                    kwargs.get("mode", "soft")
                )
            elif operation == "blame":
                return await self.blame(
                    kwargs.get("file_path"),
                    kwargs.get("line_start"),
                    kwargs.get("line_end")
                )
            else:
                raise ValueError(f"Unknown operation: {operation}")
                
        except Exception as e:
            log.error(f"Git tool error: {str(e)}")
            return {"error": str(e)}
    
    def _run_git_command(self, args: List[str], cwd: Optional[Path] = None) -> Dict[str, Any]:
        """Run Git command and return result."""
        try:
            if cwd is None:
                cwd = self.base_path
            
            cmd = [self.git_path] + args
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {"error": "Git command timed out", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def _is_git_repository(self) -> bool:
        """Check if current directory is a Git repository."""
        git_dir = self.base_path / '.git'
        return git_dir.exists() or git_dir.is_dir()
    
    async def get_status(self) -> Dict[str, Any]:
        """Get Git status."""
        try:
            result = self._run_git_command(['status', '--porcelain'])
            if not result["success"]:
                return result
            
            # Parse status output
            status_lines = result["stdout"].strip().split('\n')
            status_info = {
                "modified": [],
                "added": [],
                "deleted": [],
                "untracked": [],
                "renamed": [],
                "copied": []
            }
            
            for line in status_lines:
                if not line:
                    continue
                
                status_code = line[:2]
                file_path = line[3:]
                
                if status_code[0] in ['M', ' ']:
                    if status_code[1] == 'M':
                        status_info["modified"].append(file_path)
                    elif status_code[1] == 'A':
                        status_info["added"].append(file_path)
                    elif status_code[1] == 'D':
                        status_info["deleted"].append(file_path)
                    elif status_code[1] == '??':
                        status_info["untracked"].append(file_path)
                    elif status_code[1] == 'R':
                        status_info["renamed"].append(file_path)
                    elif status_code[1] == 'C':
                        status_info["copied"].append(file_path)
            
            # Get branch info
            branch_result = self._run_git_command(['branch', '--show-current'])
            current_branch = branch_result["stdout"].strip() if branch_result["success"] else "unknown"
            
            return {
                "branch": current_branch,
                "status": status_info,
                "is_clean": all(len(files) == 0 for files in status_info.values()),
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def get_log(self, max_count: int = 10, author: Optional[str] = None,
                     since: Optional[str] = None) -> Dict[str, Any]:
        """Get Git log."""
        try:
            args = ['log', '--oneline', '--pretty=format:%H|%an|%ad|%s', '--date=iso']
            
            if max_count:
                args.extend(['-n', str(max_count)])
            
            if author:
                args.extend(['--author', author])
            
            if since:
                args.extend(['--since', since])
            
            result = self._run_git_command(args)
            if not result["success"]:
                return result
            
            # Parse log output
            log_lines = result["stdout"].strip().split('\n')
            commits = []
            
            for line in log_lines:
                if not line:
                    continue
                
                parts = line.split('|', 3)
                if len(parts) >= 4:
                    commits.append({
                        "hash": parts[0],
                        "author": parts[1],
                        "date": parts[2],
                        "message": parts[3]
                    })
            
            return {
                "commits": commits,
                "count": len(commits),
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def get_diff(self, file_path: Optional[str] = None,
                      commit1: Optional[str] = None,
                      commit2: Optional[str] = None) -> Dict[str, Any]:
        """Get Git diff."""
        try:
            args = ['diff']
            
            if commit1 and commit2:
                args.extend([commit1, commit2])
            elif commit1:
                args.append(commit1)
            
            if file_path:
                args.append(file_path)
            
            result = self._run_git_command(args)
            if not result["success"]:
                return result
            
            return {
                "diff": result["stdout"],
                "file_path": file_path,
                "commit1": commit1,
                "commit2": commit2,
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def add_files(self, files: List[str]) -> Dict[str, Any]:
        """Add files to staging area."""
        try:
            args = ['add'] + files
            result = self._run_git_command(args)
            
            if result["success"]:
                result["message"] = f"Added {len(files)} file(s) to staging area"
            
            return result
            
        except Exception as e:
            return {"error": str(e)}
    
    async def commit(self, message: str, files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create commit."""
        try:
            if not message.strip():
                return {"error": "Commit message cannot be empty"}
            
            # Add files if specified
            if files:
                add_result = await self.add_files(files)
                if not add_result["success"]:
                    return add_result
            
            # Create commit
            args = ['commit', '-m', message]
            result = self._run_git_command(args)
            
            if result["success"]:
                result["message"] = "Commit created successfully"
            
            return result
            
        except Exception as e:
            return {"error": str(e)}
    
    async def branch_operations(self, action: str, branch_name: Optional[str] = None,
                               base_branch: Optional[str] = None) -> Dict[str, Any]:
        """Perform branch operations."""
        try:
            if action == "list":
                result = self._run_git_command(['branch', '-a'])
                if result["success"]:
                    branches = [line.strip().replace('* ', '') for line in result["stdout"].strip().split('\n') if line.strip()]
                    result["branches"] = branches
                return result
            
            elif action == "create":
                if not branch_name:
                    return {"error": "Branch name is required for create operation"}
                
                args = ['branch']
                if base_branch:
                    args.extend([branch_name, base_branch])
                else:
                    args.append(branch_name)
                
                result = self._run_git_command(args)
                if result["success"]:
                    result["message"] = f"Branch '{branch_name}' created successfully"
                return result
            
            elif action == "delete":
                if not branch_name:
                    return {"error": "Branch name is required for delete operation"}
                
                result = self._run_git_command(['branch', '-d', branch_name])
                if result["success"]:
                    result["message"] = f"Branch '{branch_name}' deleted successfully"
                return result
            
            else:
                return {"error": f"Unknown branch operation: {action}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    async def checkout(self, target: str) -> Dict[str, Any]:
        """Checkout branch or commit."""
        try:
            if not target.strip():
                return {"error": "Target is required for checkout operation"}
            
            result = self._run_git_command(['checkout', target])
            if result["success"]:
                result["message"] = f"Checked out '{target}' successfully"
            
            return result
            
        except Exception as e:
            return {"error": str(e)}
    
    async def merge(self, branch: str) -> Dict[str, Any]:
        """Merge branch."""
        try:
            if not branch.strip():
                return {"error": "Branch name is required for merge operation"}
            
            result = self._run_git_command(['merge', branch])
            if result["success"]:
                result["message"] = f"Merged branch '{branch}' successfully"
            
            return result
            
        except Exception as e:
            return {"error": str(e)}
    
    async def pull(self, remote: str = "origin", branch: Optional[str] = None) -> Dict[str, Any]:
        """Pull changes from remote."""
        try:
            args = ['pull', remote]
            if branch:
                args.append(branch)
            
            result = self._run_git_command(args)
            if result["success"]:
                result["message"] = f"Pulled changes from '{remote}' successfully"
            
            return result
            
        except Exception as e:
            return {"error": str(e)}
    
    async def push(self, remote: str = "origin", branch: Optional[str] = None) -> Dict[str, Any]:
        """Push changes to remote."""
        try:
            args = ['push', remote]
            if branch:
                args.append(branch)
            
            result = self._run_git_command(args)
            if result["success"]:
                result["message"] = f"Pushed changes to '{remote}' successfully"
            
            return result
            
        except Exception as e:
            return {"error": str(e)}
    
    async def stash_operations(self, action: str, message: Optional[str] = None) -> Dict[str, Any]:
        """Perform stash operations."""
        try:
            if action == "list":
                result = self._run_git_command(['stash', 'list'])
                if result["success"]:
                    stashes = [line.strip() for line in result["stdout"].strip().split('\n') if line.strip()]
                    result["stashes"] = stashes
                return result
            
            elif action == "save":
                args = ['stash']
                if message:
                    args.extend(['push', '-m', message])
                else:
                    args.append('push')
                
                result = self._run_git_command(args)
                if result["success"]:
                    result["message"] = "Changes stashed successfully"
                return result
            
            elif action == "pop":
                result = self._run_git_command(['stash', 'pop'])
                if result["success"]:
                    result["message"] = "Stash popped successfully"
                return result
            
            elif action == "apply":
                result = self._run_git_command(['stash', 'apply'])
                if result["success"]:
                    result["message"] = "Stash applied successfully"
                return result
            
            elif action == "drop":
                result = self._run_git_command(['stash', 'drop'])
                if result["success"]:
                    result["message"] = "Stash dropped successfully"
                return result
            
            else:
                return {"error": f"Unknown stash operation: {action}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    async def reset(self, target: str = "HEAD", mode: str = "soft") -> Dict[str, Any]:
        """Reset to target commit."""
        try:
            if mode not in ["soft", "mixed", "hard"]:
                return {"error": "Reset mode must be 'soft', 'mixed', or 'hard'"}
            
            args = ['reset', f'--{mode}', target]
            result = self._run_git_command(args)
            
            if result["success"]:
                result["message"] = f"Reset to '{target}' ({mode} mode) successfully"
            
            return result
            
        except Exception as e:
            return {"error": str(e)}
    
    async def blame(self, file_path: str, line_start: Optional[int] = None,
                   line_end: Optional[int] = None) -> Dict[str, Any]:
        """Get blame information for file."""
        try:
            if not file_path.strip():
                return {"error": "File path is required for blame operation"}
            
            args = ['blame', '--line-porcelain']
            if line_start and line_end:
                args.extend(['-L', f'{line_start},{line_end}'])
            args.append(file_path)
            
            result = self._run_git_command(args)
            if not result["success"]:
                return result
            
            # Parse blame output
            blame_lines = result["stdout"].strip().split('\n')
            blame_info = []
            current_blame = {}
            
            for line in blame_lines:
                if line.startswith('\t'):
                    # This is the code line
                    if current_blame:
                        current_blame['code'] = line[1:]  # Remove tab
                        blame_info.append(current_blame)
                        current_blame = {}
                elif line:
                    # Parse blame metadata
                    parts = line.split(' ', 1)
                    if len(parts) >= 2:
                        key = parts[0]
                        value = parts[1]
                        if key.isdigit():  # This is the commit hash
                            current_blame['commit'] = key
                        else:
                            current_blame[key] = value
            
            return {
                "file_path": file_path,
                "blame_info": blame_info,
                "line_start": line_start,
                "line_end": line_end,
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def description(self) -> str:
        """Get tool description."""
        return "Git version control operations including status, log, diff, branch, commit, and remote operations"
    
    def parameters(self) -> Dict[str, Any]:
        """Get tool parameter schema."""
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": [
                        "status", "log", "diff", "add", "commit", "branch",
                        "checkout", "merge", "pull", "push", "stash", "reset", "blame"
                    ]
                },
                "files": {"type": "array", "items": {"type": "string"}},
                "message": {"type": "string"},
                "max_count": {"type": "integer"},
                "author": {"type": "string"},
                "since": {"type": "string"},
                "file_path": {"type": "string"},
                "commit1": {"type": "string"},
                "commit2": {"type": "string"},
                "action": {"type": "string"},
                "branch_name": {"type": "string"},
                "base_branch": {"type": "string"},
                "target": {"type": "string"},
                "branch": {"type": "string"},
                "remote": {"type": "string"},
                "mode": {"type": "string"},
                "line_start": {"type": "integer"},
                "line_end": {"type": "integer"}
            },
            "required": ["operation"]
        }