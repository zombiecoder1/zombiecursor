"""
System tool for system information and operations.
"""
import os
import platform
import subprocess
import psutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from core.interfaces import Tool
from core.config import settings
from core.logging_config import log


class SystemTool(Tool):
    """Tool for system information and operations."""
    
    def __init__(self):
        self.base_path = Path(settings.project_root).resolve()
    
    async def execute(self, operation: str, **kwargs) -> Any:
        """Execute system operation."""
        try:
            if operation == "get_system_info":
                return await self.get_system_info()
            elif operation == "get_process_info":
                return await self.get_process_info()
            elif operation == "get_disk_usage":
                return await self.get_disk_usage(kwargs.get("path", "."))
            elif operation == "get_memory_usage":
                return await self.get_memory_usage()
            elif operation == "get_network_info":
                return await self.get_network_info()
            elif operation == "list_processes":
                return await self.list_processes(kwargs.get("limit", 50))
            elif operation == "kill_process":
                return await self.kill_process(kwargs.get("pid"))
            elif operation == "run_command":
                return await self.run_command(
                    kwargs.get("command"),
                    kwargs.get("shell", True),
                    kwargs.get("timeout", 30)
                )
            elif operation == "get_environment":
                return await self.get_environment(kwargs.get("filter"))
            elif operation == "set_environment":
                return await self.set_environment(
                    kwargs.get("key"),
                    kwargs.get("value")
                )
            elif operation == "get_path_info":
                return await self.get_path_info(kwargs.get("path", "."))
            elif operation == "check_port":
                return await self.check_port(kwargs.get("port"), kwargs.get("host", "localhost"))
            elif operation == "get_file_descriptors":
                return await self.get_file_descriptors(kwargs.get("pid"))
            else:
                raise ValueError(f"Unknown operation: {operation}")
                
        except Exception as e:
            log.error(f"System tool error: {str(e)}")
            return {"error": str(e)}
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information."""
        try:
            info = {
                "platform": {
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                    "architecture": platform.architecture(),
                    "python_version": platform.python_version(),
                    "python_implementation": platform.python_implementation()
                },
                "boot_time": psutil.boot_time(),
                "current_user": {
                    "name": psutil.users()[0].name if psutil.users() else "unknown",
                    "terminal": psutil.users()[0].terminal if psutil.users() else "unknown",
                    "host": psutil.users()[0].host if psutil.users() else "unknown"
                }
            }
            
            return {
                "system_info": info,
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def get_process_info(self) -> Dict[str, Any]:
        """Get current process information."""
        try:
            process = psutil.Process()
            
            info = {
                "pid": process.pid,
                "name": process.name(),
                "status": process.status(),
                "create_time": process.create_time(),
                "cpu_percent": process.cpu_percent(),
                "memory_info": process.memory_info()._asdict(),
                "memory_percent": process.memory_percent(),
                "num_threads": process.num_threads(),
                "num_fds": process.num_fds() if hasattr(process, 'num_fds') else None,
                "cwd": process.cwd(),
                "exe": process.exe(),
                "cmdline": process.cmdline(),
                "environ": dict(process.environ()),
                "connections": [conn._asdict() for conn in process.connections()],
                "threads": [thread._asdict() for thread in process.threads()]
            }
            
            return {
                "process_info": info,
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def get_disk_usage(self, path: str = ".") -> Dict[str, Any]:
        """Get disk usage information."""
        try:
            target_path = Path(path).resolve()
            
            if not target_path.exists():
                return {"error": f"Path does not exist: {path}"}
            
            # Get disk usage for the path
            disk_usage = psutil.disk_usage(str(target_path))
            
            # Get partition information
            partitions = psutil.disk_partitions()
            partition_info = None
            
            for partition in partitions:
                if target_path.is_relative_to(Path(partition.mountpoint)):
                    partition_info = partition._asdict()
                    break
            
            usage_info = {
                "path": str(target_path),
                "total": disk_usage.total,
                "used": disk_usage.used,
                "free": disk_usage.free,
                "percent_used": (disk_usage.used / disk_usage.total) * 100,
                "partition": partition_info
            }
            
            return {
                "disk_usage": usage_info,
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage information."""
        try:
            # Virtual memory
            virtual_memory = psutil.virtual_memory()
            
            # Swap memory
            swap_memory = psutil.swap_memory()
            
            memory_info = {
                "virtual": virtual_memory._asdict(),
                "swap": swap_memory._asdict()
            }
            
            return {
                "memory_info": memory_info,
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def get_network_info(self) -> Dict[str, Any]:
        """Get network information."""
        try:
            # Network I/O counters
            net_io = psutil.net_io_counters()
            
            # Network interfaces
            net_interfaces = psutil.net_if_addrs()
            net_stats = psutil.net_if_stats()
            
            # Network connections
            connections = psutil.net_connections()
            
            network_info = {
                "io_counters": net_io._asdict(),
                "interfaces": {
                    name: [addr._asdict() for addr in addrs]
                    for name, addrs in net_interfaces.items()
                },
                "interface_stats": {
                    name: stats._asdict()
                    for name, stats in net_stats.items()
                },
                "connections": [conn._asdict() for conn in connections[:100]]  # Limit to 100
            }
            
            return {
                "network_info": network_info,
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def list_processes(self, limit: int = 50) -> Dict[str, Any]:
        """List running processes."""
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent']):
                try:
                    process_info = proc.info
                    processes.append(process_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Sort by CPU usage and limit
            processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            processes = processes[:limit]
            
            return {
                "processes": processes,
                "count": len(processes),
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def kill_process(self, pid: int) -> Dict[str, Any]:
        """Kill a process."""
        try:
            if not isinstance(pid, int) or pid <= 0:
                return {"error": "Invalid PID provided"}
            
            process = psutil.Process(pid)
            process.terminate()
            
            # Wait a bit to see if it terminated
            try:
                process.wait(timeout=5)
                message = f"Process {pid} terminated successfully"
            except psutil.TimeoutExpired:
                # Force kill if terminate didn't work
                process.kill()
                message = f"Process {pid} force killed"
            
            return {
                "message": message,
                "pid": pid,
                "success": True
            }
            
        except psutil.NoSuchProcess:
            return {"error": f"Process {pid} does not exist"}
        except psutil.AccessDenied:
            return {"error": f"Access denied to kill process {pid}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def run_command(self, command: str, shell: bool = True, timeout: int = 30) -> Dict[str, Any]:
        """Run system command."""
        try:
            if not command.strip():
                return {"error": "Empty command provided"}
            
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.base_path
            )
            
            return {
                "command": command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0,
                "timeout": False
            }
            
        except subprocess.TimeoutExpired:
            return {
                "error": f"Command timed out after {timeout} seconds",
                "timeout": True,
                "success": False
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def get_environment(self, filter_key: Optional[str] = None) -> Dict[str, Any]:
        """Get environment variables."""
        try:
            env_vars = dict(os.environ)
            
            if filter_key:
                filtered_vars = {k: v for k, v in env_vars.items() if filter_key.lower() in k.lower()}
                return {
                    "environment_variables": filtered_vars,
                    "filter": filter_key,
                    "count": len(filtered_vars),
                    "success": True
                }
            else:
                return {
                    "environment_variables": env_vars,
                    "count": len(env_vars),
                    "success": True
                }
                
        except Exception as e:
            return {"error": str(e)}
    
    async def set_environment(self, key: str, value: str) -> Dict[str, Any]:
        """Set environment variable."""
        try:
            if not key.strip():
                return {"error": "Environment variable key cannot be empty"}
            
            os.environ[key] = value
            
            return {
                "message": f"Environment variable '{key}' set successfully",
                "key": key,
                "value": value,
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def get_path_info(self, path: str = ".") -> Dict[str, Any]:
        """Get detailed path information."""
        try:
            target_path = Path(path).resolve()
            
            if not target_path.exists():
                return {"error": f"Path does not exist: {path}"}
            
            stat_info = target_path.stat()
            
            path_info = {
                "path": str(target_path),
                "name": target_path.name,
                "parent": str(target_path.parent),
                "suffix": target_path.suffix,
                "stem": target_path.stem,
                "exists": target_path.exists(),
                "is_file": target_path.is_file(),
                "is_dir": target_path.is_dir(),
                "is_symlink": target_path.is_symlink(),
                "is_absolute": target_path.is_absolute(),
                "stat": {
                    "size": stat_info.st_size,
                    "mode": stat_info.st_mode,
                    "uid": stat_info.st_uid,
                    "gid": stat_info.st_gid,
                    "atime": stat_info.st_atime,
                    "mtime": stat_info.st_mtime,
                    "ctime": stat_info.st_ctime
                }
            }
            
            # Resolve symlink if it is one
            if target_path.is_symlink():
                path_info["symlink_target"] = str(target_path.resolve())
            
            return {
                "path_info": path_info,
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def check_port(self, port: int, host: str = "localhost") -> Dict[str, Any]:
        """Check if a port is in use."""
        try:
            if not isinstance(port, int) or port <= 0 or port > 65535:
                return {"error": "Invalid port number"}
            
            import socket
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            
            result = sock.connect_ex((host, port))
            sock.close()
            
            is_open = result == 0
            
            # If port is open, try to get the process using it
            process_info = None
            if is_open:
                for conn in psutil.net_connections():
                    if (conn.laddr.port == port and 
                        conn.status == 'LISTEN' and 
                        conn.pid):
                        try:
                            proc = psutil.Process(conn.pid)
                            process_info = {
                                "pid": conn.pid,
                                "name": proc.name(),
                                "cmdline": proc.cmdline()
                            }
                            break
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            break
            
            return {
                "port": port,
                "host": host,
                "is_open": is_open,
                "process": process_info,
                "success": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def get_file_descriptors(self, pid: Optional[int] = None) -> Dict[str, Any]:
        """Get file descriptors for a process."""
        try:
            if pid is None:
                pid = os.getpid()
            
            process = psutil.Process(pid)
            
            if hasattr(process, 'open_files'):
                open_files = [f._asdict() for f in process.open_files()]
            else:
                open_files = []
            
            return {
                "pid": pid,
                "open_files": open_files,
                "count": len(open_files),
                "success": True
            }
            
        except psutil.NoSuchProcess:
            return {"error": f"Process {pid} does not exist"}
        except Exception as e:
            return {"error": str(e)}
    
    def description(self) -> str:
        """Get tool description."""
        return "System information and operations including process management, disk usage, memory, network, and environment variables"
    
    def parameters(self) -> Dict[str, Any]:
        """Get tool parameter schema."""
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": [
                        "get_system_info", "get_process_info", "get_disk_usage",
                        "get_memory_usage", "get_network_info", "list_processes",
                        "kill_process", "run_command", "get_environment",
                        "set_environment", "get_path_info", "check_port",
                        "get_file_descriptors"
                    ]
                },
                "path": {"type": "string"},
                "limit": {"type": "integer"},
                "pid": {"type": "integer"},
                "command": {"type": "string"},
                "shell": {"type": "boolean"},
                "timeout": {"type": "integer"},
                "filter": {"type": "string"},
                "key": {"type": "string"},
                "value": {"type": "string"},
                "host": {"type": "string"},
                "port": {"type": "integer"}
            },
            "required": ["operation"]
        }