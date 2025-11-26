"""
Tool integration and management for the Coder Agent.
"""
from typing import Dict, Any, List, Optional
from tools.fs_tool import FilesystemTool
from tools.python_tool import PythonTool
from tools.search_tool import SearchTool
from tools.git_tool import GitTool
from tools.system_tool import SystemTool
from core.logging_config import log


class ToolManager:
    """Manages tool integration for the Coder Agent."""
    
    def __init__(self):
        self.tools = {
            "filesystem": FilesystemTool(),
            "python": PythonTool(),
            "search": SearchTool(),
            "git": GitTool(),
            "system": SystemTool()
        }
        
        # Tool categories for better organization
        self.tool_categories = {
            "file_operations": ["filesystem"],
            "code_execution": ["python"],
            "code_analysis": ["search"],
            "version_control": ["git"],
            "system_info": ["system"]
        }
        
        log.info("Tool Manager initialized with tools: %s", list(self.tools.keys()))
    
    async def execute_tool(self, tool_name: str, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute a specific tool operation."""
        if tool_name not in self.tools:
            return {"error": f"Unknown tool: {tool_name}"}
        
        try:
            tool = self.tools[tool_name]
            result = await tool.execute(operation, **kwargs)
            
            # Log tool usage
            log.info(f"Tool executed: {tool_name}.{operation}")
            
            return result
            
        except Exception as e:
            log.error(f"Tool execution error: {tool_name}.{operation} - {str(e)}")
            return {"error": str(e)}
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific tool."""
        if tool_name not in self.tools:
            return None
        
        tool = self.tools[tool_name]
        return {
            "name": tool_name,
            "description": tool.description(),
            "parameters": tool.parameters()
        }
    
    def get_all_tools_info(self) -> Dict[str, Any]:
        """Get information about all available tools."""
        tools_info = {}
        for name in self.tools:
            tools_info[name] = self.get_tool_info(name)
        return tools_info
    
    def get_tools_by_category(self, category: str) -> List[str]:
        """Get tools by category."""
        return self.tool_categories.get(category, [])
    
    async def batch_execute(self, operations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple tool operations in batch."""
        results = []
        
        for op in operations:
            tool_name = op.get("tool")
            operation = op.get("operation")
            params = op.get("params", {})
            
            result = await self.execute_tool(tool_name, operation, **params)
            results.append({
                "tool": tool_name,
                "operation": operation,
                "result": result
            })
        
        return results
    
    async def smart_file_analysis(self, file_path: str) -> Dict[str, Any]:
        """Perform smart analysis of a file using multiple tools."""
        analysis = {
            "file_path": file_path,
            "basic_info": None,
            "content_analysis": None,
            "dependencies": None,
            "git_info": None
        }
        
        try:
            # Get basic file info
            fs_result = await self.execute_tool("filesystem", "file_info", path=file_path)
            if fs_result.get("success"):
                analysis["basic_info"] = fs_result.get("info")
            
            # Read file content for analysis
            read_result = await self.execute_tool("filesystem", "read_file", path=file_path)
            if read_result.get("success"):
                content = read_result.get("content", "")
                
                # Analyze imports/dependencies
                if file_path.endswith('.py'):
                    imports = []
                    lines = content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line.startswith('import ') or line.startswith('from '):
                            imports.append(line)
                    analysis["dependencies"] = imports
                
                # Search for functions and classes
                search_functions = await self.execute_tool(
                    "search", "search_functions", 
                    function_name="", 
                    directory=file_path[:file_path.rfind('/')],
                    file_patterns=[file_path.split('/')[-1]]
                )
                
                search_classes = await self.execute_tool(
                    "search", "search_classes",
                    class_name="",
                    directory=file_path[:file_path.rfind('/')],
                    file_patterns=[file_path.split('/')[-1]]
                )
                
                analysis["content_analysis"] = {
                    "functions": search_functions.get("matches", []),
                    "classes": search_classes.get("matches", []),
                    "line_count": len(content.split('\n')),
                    "char_count": len(content)
                }
            
            # Get git information if available
            git_result = await self.execute_tool("git", "blame", file_path=file_path)
            if git_result.get("success"):
                analysis["git_info"] = {
                    "blame_info": git_result.get("blame_info", [])[:10]  # Limit to first 10 lines
                }
            
            return {
                "success": True,
                "analysis": analysis
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "partial_analysis": analysis
            }
    
    async def code_review_helper(self, file_path: str) -> Dict[str, Any]:
        """Helper for code review using multiple tools."""
        review = {
            "file_path": file_path,
            "syntax_check": None,
            "style_issues": None,
            "security_issues": None,
            "performance_suggestions": None
        }
        
        try:
            # Read file
            read_result = await self.execute_tool("filesystem", "read_file", path=file_path)
            if not read_result.get("success"):
                return {"success": False, "error": "Cannot read file"}
            
            content = read_result.get("content", "")
            
            # Syntax check for Python files
            if file_path.endswith('.py'):
                syntax_result = await self.execute_tool("python", "check_syntax", code=content)
                review["syntax_check"] = syntax_result
                
                # Style check
                try:
                    lint_result = await self.execute_tool("python", "lint_code", code=content, linter="flake8")
                    review["style_issues"] = lint_result
                except:
                    review["style_issues"] = {"error": "Linting not available"}
            
            # Security analysis (basic)
            security_issues = []
            if "password" in content.lower() or "secret" in content.lower():
                security_issues.append("Potential hardcoded secrets detected")
            
            if "eval(" in content or "exec(" in content:
                security_issues.append("Dynamic code execution detected")
            
            review["security_issues"] = {
                "issues": security_issues,
                "count": len(security_issues)
            }
            
            # Performance suggestions (basic)
            performance_suggestions = []
            if file_path.endswith('.py'):
                if "for i in range(len(" in content:
                    performance_suggestions.append("Consider using enumerate() instead of range(len())")
                
                if content.count("import ") > 10:
                    performance_suggestions.append("Many imports - consider if all are necessary")
            
            review["performance_suggestions"] = {
                "suggestions": performance_suggestions,
                "count": len(performance_suggestions)
            }
            
            return {
                "success": True,
                "review": review
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "partial_review": review
            }
    
    def get_tool_recommendations(self, query: str) -> List[str]:
        """Get tool recommendations based on query."""
        query_lower = query.lower()
        recommendations = []
        
        # File operations
        if any(word in query_lower for word in ["file", "read", "write", "create", "delete", "folder"]):
            recommendations.append("filesystem")
        
        # Code execution
        if any(word in query_lower for word in ["run", "execute", "python", "code", "test"]):
            recommendations.append("python")
        
        # Search operations
        if any(word in query_lower for word in ["search", "find", "look for", "where", "locate"]):
            recommendations.append("search")
        
        # Git operations
        if any(word in query_lower for word in ["git", "commit", "push", "pull", "branch", "merge"]):
            recommendations.append("git")
        
        # System operations
        if any(word in query_lower for word in ["system", "process", "memory", "disk", "cpu"]):
            recommendations.append("system")
        
        return recommendations if recommendations else ["filesystem", "search"]  # Default recommendations