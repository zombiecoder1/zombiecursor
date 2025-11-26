"""
Python execution tool for running Python code safely.
"""
import subprocess
import sys
import tempfile
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from core.interfaces import Tool
from core.config import settings
from core.logging_config import log


class PythonTool(Tool):
    """Tool for safe Python code execution."""
    
    def __init__(self):
        self.timeout = settings.python_timeout
        self.temp_dir = Path(tempfile.gettempdir()) / "zombiecursor_python"
        self.temp_dir.mkdir(exist_ok=True)
    
    async def execute(self, operation: str, **kwargs) -> Any:
        """Execute Python operation."""
        try:
            if operation == "run_code":
                return await self.run_code(
                    kwargs.get("code"),
                    kwargs.get("capture_output", True),
                    kwargs.get("timeout", self.timeout)
                )
            elif operation == "check_syntax":
                return await self.check_syntax(kwargs.get("code"))
            elif operation == "format_code":
                return await self.format_code(
                    kwargs.get("code"),
                    kwargs.get("formatter", "black")
                )
            elif operation == "lint_code":
                return await self.lint_code(
                    kwargs.get("code"),
                    kwargs.get("linter", "flake8")
                )
            elif operation == "install_package":
                return await self.install_package(
                    kwargs.get("package"),
                    kwargs.get("upgrade", False)
                )
            elif operation == "list_packages":
                return await self.list_packages()
            else:
                raise ValueError(f"Unknown operation: {operation}")
                
        except Exception as e:
            log.error(f"Python tool error: {str(e)}")
            return {"error": str(e)}
    
    async def run_code(self, code: str, capture_output: bool = True, 
                      timeout: Optional[int] = None) -> Dict[str, Any]:
        """Run Python code safely."""
        try:
            if not code.strip():
                return {"error": "Empty code provided"}
            
            # Create temporary file
            temp_file = self.temp_dir / f"temp_{asyncio.current_task().get_name() or 'unknown'}.py"
            
            try:
                # Write code to temporary file
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(code)
                
                # Prepare command
                cmd = [sys.executable, str(temp_file)]
                
                # Execute with timeout
                if timeout is None:
                    timeout = self.timeout
                
                if capture_output:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        cwd=self.temp_dir
                    )
                    
                    return {
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "returncode": result.returncode,
                        "success": result.returncode == 0,
                        "timeout": False
                    }
                else:
                    # For non-captured output, we'll run it differently
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        cwd=self.temp_dir
                    )
                    
                    try:
                        stdout, stderr = await asyncio.wait_for(
                            process.communicate(), 
                            timeout=timeout
                        )
                        
                        return {
                            "stdout": stdout.decode('utf-8') if stdout else "",
                            "stderr": stderr.decode('utf-8') if stderr else "",
                            "returncode": process.returncode,
                            "success": process.returncode == 0,
                            "timeout": False
                        }
                    except asyncio.TimeoutError:
                        process.kill()
                        await process.wait()
                        return {
                            "error": f"Code execution timed out after {timeout} seconds",
                            "timeout": True,
                            "success": False
                        }
            
            finally:
                # Clean up temporary file
                if temp_file.exists():
                    temp_file.unlink()
            
        except subprocess.TimeoutExpired:
            return {
                "error": f"Code execution timed out after {timeout} seconds",
                "timeout": True,
                "success": False
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def check_syntax(self, code: str) -> Dict[str, Any]:
        """Check Python code syntax."""
        try:
            if not code.strip():
                return {"error": "Empty code provided"}
            
            # Compile the code to check syntax
            compile(code, '<string>', 'exec')
            
            return {
                "message": "Syntax is valid",
                "valid": True,
                "success": True
            }
            
        except SyntaxError as e:
            return {
                "error": f"Syntax error: {e.msg}",
                "line": e.lineno,
                "column": e.offset,
                "valid": False,
                "success": True
            }
        except Exception as e:
            return {"error": str(e), "valid": False}
    
    async def format_code(self, code: str, formatter: str = "black") -> Dict[str, Any]:
        """Format Python code."""
        try:
            if not code.strip():
                return {"error": "Empty code provided"}
            
            if formatter == "black":
                return await self._format_with_black(code)
            elif formatter == "autopep8":
                return await self._format_with_autopep8(code)
            else:
                return {"error": f"Unsupported formatter: {formatter}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    async def _format_with_black(self, code: str) -> Dict[str, Any]:
        """Format code with black."""
        try:
            import black
            
            # Parse and format the code
            try:
                formatted = black.format_str(code, mode=black.FileMode())
                return {
                    "formatted_code": formatted,
                    "original_code": code,
                    "changed": formatted != code,
                    "formatter": "black",
                    "success": True
                }
            except black.InvalidInput:
                return {"error": "Invalid Python code for black formatting"}
                
        except ImportError:
            return {"error": "black is not installed"}
        except Exception as e:
            return {"error": str(e)}
    
    async def _format_with_autopep8(self, code: str) -> Dict[str, Any]:
        """Format code with autopep8."""
        try:
            import autopep8
            
            formatted = autopep8.fix_code(code)
            return {
                "formatted_code": formatted,
                "original_code": code,
                "changed": formatted != code,
                "formatter": "autopep8",
                "success": True
            }
            
        except ImportError:
            return {"error": "autopep8 is not installed"}
        except Exception as e:
            return {"error": str(e)}
    
    async def lint_code(self, code: str, linter: str = "flake8") -> Dict[str, Any]:
        """Lint Python code."""
        try:
            if not code.strip():
                return {"error": "Empty code provided"}
            
            if linter == "flake8":
                return await self._lint_with_flake8(code)
            elif linter == "pylint":
                return await self._lint_with_pylint(code)
            else:
                return {"error": f"Unsupported linter: {linter}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    async def _lint_with_flake8(self, code: str) -> Dict[str, Any]:
        """Lint code with flake8."""
        try:
            from flake8.api import legacy as flake8
            
            # Create temporary file
            temp_file = self.temp_dir / f"lint_{asyncio.current_task().get_name() or 'unknown'}.py"
            
            try:
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(code)
                
                # Run flake8
                style_guide = flake8.get_style_guide()
                report = style_guide.input_file(str(temp_file))
                
                # Get results
                results = []
                for error in report.get_statistics():
                    results.append(str(error))
                
                return {
                    "issues": results,
                    "error_count": len(results),
                    "linter": "flake8",
                    "success": True
                }
            
            finally:
                if temp_file.exists():
                    temp_file.unlink()
                    
        except ImportError:
            return {"error": "flake8 is not installed"}
        except Exception as e:
            return {"error": str(e)}
    
    async def _lint_with_pylint(self, code: str) -> Dict[str, Any]:
        """Lint code with pylint."""
        try:
            from pylint import lint
            from io import StringIO
            
            # Create temporary file
            temp_file = self.temp_dir / f"lint_{asyncio.current_task().get_name() or 'unknown'}.py"
            
            try:
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(code)
                
                # Capture pylint output
                output = StringIO()
                reporter = lint.TextReporter(output)
                
                # Run pylint
                lint.Run([str(temp_file)], reporter=reporter, exit=False)
                
                # Parse results
                pylint_output = output.getvalue()
                lines = pylint_output.split('\n')
                
                issues = []
                for line in lines:
                    if line.strip() and ':' in line:
                        issues.append(line.strip())
                
                return {
                    "issues": issues,
                    "error_count": len(issues),
                    "linter": "pylint",
                    "success": True
                }
            
            finally:
                if temp_file.exists():
                    temp_file.unlink()
                    
        except ImportError:
            return {"error": "pylint is not installed"}
        except Exception as e:
            return {"error": str(e)}
    
    async def install_package(self, package: str, upgrade: bool = False) -> Dict[str, Any]:
        """Install Python package."""
        try:
            if not package.strip():
                return {"error": "Empty package name provided"}
            
            cmd = [sys.executable, "-m", "pip", "install"]
            if upgrade:
                cmd.append("--upgrade")
            cmd.append(package)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0,
                "package": package,
                "upgrade": upgrade
            }
            
        except subprocess.TimeoutExpired:
            return {"error": "Package installation timed out"}
        except Exception as e:
            return {"error": str(e)}
    
    async def list_packages(self) -> Dict[str, Any]:
        """List installed packages."""
        try:
            cmd = [sys.executable, "-m", "pip", "list", "--format=json"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                import json
                packages = json.loads(result.stdout)
                return {
                    "packages": packages,
                    "count": len(packages),
                    "success": True
                }
            else:
                return {"error": result.stderr}
                
        except Exception as e:
            return {"error": str(e)}
    
    def description(self) -> str:
        """Get tool description."""
        return "Python code execution, syntax checking, formatting, linting, and package management"
    
    def parameters(self) -> Dict[str, Any]:
        """Get tool parameter schema."""
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": [
                        "run_code", "check_syntax", "format_code", 
                        "lint_code", "install_package", "list_packages"
                    ]
                },
                "code": {"type": "string"},
                "capture_output": {"type": "boolean"},
                "timeout": {"type": "integer"},
                "formatter": {"type": "string"},
                "linter": {"type": "string"},
                "package": {"type": "string"},
                "upgrade": {"type": "boolean"}
            },
            "required": ["operation"]
        }