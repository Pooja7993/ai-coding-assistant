"""
Plugin system for the AI Coding Assistant.
Allows dynamic loading and registration of tools and capabilities.
"""
import logging
import inspect
import importlib
import os
from typing import Dict, Any, List, Callable, Optional, Type
from abc import ABC, abstractmethod
from pydantic import BaseModel
from pathlib import Path

logger = logging.getLogger(__name__)


class PluginMetadata(BaseModel):
    """Metadata for a plugin."""
    name: str
    version: str
    description: str
    author: str
    category: str = "general"
    dependencies: List[str] = []
    enabled: bool = True


class ToolResult(BaseModel):
    """Result from a tool execution."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}


class BaseTool(ABC):
    """Base class for all tools."""
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Tool metadata."""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool."""
        pass
    
    def validate_params(self, **kwargs) -> bool:
        """Validate tool parameters."""
        return True
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's parameter schema."""
        sig = inspect.signature(self.execute)
        schema = {
            "name": self.metadata.name,
            "description": self.metadata.description,
            "parameters": {}
        }
        
        for param_name, param in sig.parameters.items():
            if param_name != "kwargs":
                param_info = {
                    "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any",
                    "required": param.default == inspect.Parameter.empty
                }
                if param.default != inspect.Parameter.empty:
                    param_info["default"] = param.default
                schema["parameters"][param_name] = param_info
        
        return schema


class CodeAnalyzerTool(BaseTool):
    """Tool for analyzing code quality and complexity."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="code_analyzer",
            version="1.0.0",
            description="Analyze code quality, complexity, and potential issues",
            author="AI Assistant Team",
            category="code_analysis"
        )
    
    async def execute(self, code: str, language: str = "python") -> ToolResult:
        """Analyze the given code."""
        try:
            # Simple analysis - in production, use more sophisticated tools
            lines = code.split('\n')
            
            analysis = {
                "line_count": len(lines),
                "complexity_score": self._calculate_complexity(code),
                "issues": self._find_issues(code, language),
                "suggestions": self._get_suggestions(code, language)
            }
            
            return ToolResult(
                success=True,
                data=analysis,
                metadata={"language": language}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e)
            )
    
    def _calculate_complexity(self, code: str) -> int:
        """Calculate a simple complexity score."""
        complexity_keywords = ["if", "elif", "else", "for", "while", "try", "except", "with"]
        complexity = 1  # Base complexity
        
        for keyword in complexity_keywords:
            complexity += code.count(keyword)
        
        return complexity
    
    def _find_issues(self, code: str, language: str) -> List[str]:
        """Find potential issues in the code."""
        issues = []
        
        if language.lower() == "python":
            if "TODO" in code or "FIXME" in code:
                issues.append("Contains TODO/FIXME comments")
            if code.count("except:") > 0:
                issues.append("Bare except clause detected")
            if "import *" in code:
                issues.append("Wildcard import detected")
        
        return issues
    
    def _get_suggestions(self, code: str, language: str) -> List[str]:
        """Get improvement suggestions."""
        suggestions = []
        
        if language.lower() == "python":
            if not any(line.strip().startswith('"""') or line.strip().startswith("'''") for line in code.split('\n')):
                suggestions.append("Consider adding docstrings to functions")
            if "print(" in code:
                suggestions.append("Consider using logging instead of print statements")
        
        return suggestions


class DependencyInstallerTool(BaseTool):
    """Tool for automatically installing missing dependencies."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="dependency_installer",
            version="1.0.0",
            description="Automatically detect and install missing Python dependencies",
            author="AI Assistant Team",
            category="package_management"
        )
    
    async def execute(self, code: str, language: str = "python") -> ToolResult:
        """Detect and install missing dependencies."""
        try:
            if language.lower() != "python":
                return ToolResult(
                    success=False,
                    error="Only Python dependency installation is currently supported"
                )
            
            imports = self._extract_imports(code)
            missing_packages = []
            
            for imp in imports:
                if not self._is_package_installed(imp):
                    missing_packages.append(imp)
            
            if missing_packages:
                installation_results = []
                for package in missing_packages:
                    result = await self._install_package(package)
                    installation_results.append(result)
                
                return ToolResult(
                    success=True,
                    data={
                        "missing_packages": missing_packages,
                        "installation_results": installation_results
                    }
                )
            else:
                return ToolResult(
                    success=True,
                    data={"message": "All dependencies are already installed"}
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e)
            )
    
    def _extract_imports(self, code: str) -> List[str]:
        """Extract import statements from code."""
        imports = []
        lines = code.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('import '):
                module = line.replace('import ', '').split()[0]
                imports.append(module.split('.')[0])
            elif line.startswith('from '):
                module = line.split()[1]
                imports.append(module.split('.')[0])
        
        # Filter out standard library modules
        stdlib_modules = {
            'os', 'sys', 'json', 'datetime', 're', 'math', 'random', 
            'collections', 'itertools', 'functools', 'pathlib', 'logging'
        }
        
        return [imp for imp in imports if imp not in stdlib_modules]
    
    def _is_package_installed(self, package: str) -> bool:
        """Check if a package is installed."""
        try:
            importlib.import_module(package)
            return True
        except ImportError:
            return False
    
    async def _install_package(self, package: str) -> Dict[str, Any]:
        """Install a package using pip."""
        import subprocess
        import asyncio
        
        try:
            process = await asyncio.create_subprocess_exec(
                'pip', 'install', package,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                "package": package,
                "success": process.returncode == 0,
                "stdout": stdout.decode(),
                "stderr": stderr.decode()
            }
        except Exception as e:
            return {
                "package": package,
                "success": False,
                "error": str(e)
            }


class TestGeneratorTool(BaseTool):
    """Tool for generating unit tests."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="test_generator",
            version="1.0.0",
            description="Generate unit tests for code",
            author="AI Assistant Team",
            category="testing"
        )
    
    async def execute(self, code: str, language: str = "python", framework: str = "pytest") -> ToolResult:
        """Generate unit tests for the given code."""
        try:
            if language.lower() != "python":
                return ToolResult(
                    success=False,
                    error="Only Python test generation is currently supported"
                )
            
            functions = self._extract_functions(code)
            test_code = self._generate_test_code(functions, framework)
            
            return ToolResult(
                success=True,
                data={
                    "test_code": test_code,
                    "functions_tested": len(functions),
                    "framework": framework
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e)
            )
    
    def _extract_functions(self, code: str) -> List[Dict[str, Any]]:
        """Extract function definitions from code."""
        functions = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('def ') and '(' in stripped:
                func_name = stripped.split('def ')[1].split('(')[0].strip()
                if not func_name.startswith('_'):  # Skip private functions
                    functions.append({
                        "name": func_name,
                        "line": i + 1,
                        "signature": stripped
                    })
        
        return functions
    
    def _generate_test_code(self, functions: List[Dict[str, Any]], framework: str) -> str:
        """Generate test code for functions."""
        if framework == "pytest":
            test_code = "import pytest\nfrom your_module import *\n\n"
            
            for func in functions:
                test_code += f"def test_{func['name']}():\n"
                test_code += f"    # Test {func['name']} function\n"
                test_code += f"    # TODO: Implement test for {func['name']}\n"
                test_code += f"    assert True  # Placeholder\n\n"
            
            return test_code
        else:
            return "# Unsupported test framework"


class PluginManager:
    """Manager for loading and executing plugins."""
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.plugins_dir = Path("plugins")
        self._load_builtin_tools()
    
    def _load_builtin_tools(self):
        """Load built-in tools."""
        builtin_tools = [
            CodeAnalyzerTool(),
            DependencyInstallerTool(),
            TestGeneratorTool()
        ]
        
        for tool in builtin_tools:
            self.register_tool(tool)
    
    def register_tool(self, tool: BaseTool):
        """Register a new tool."""
        if not isinstance(tool, BaseTool):
            raise ValueError("Tool must inherit from BaseTool")
        
        tool_name = tool.metadata.name
        if tool_name in self.tools:
            logger.warning(f"Tool {tool_name} already registered, overwriting")
        
        self.tools[tool_name] = tool
        logger.info(f"Registered tool: {tool_name}")
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools."""
        return [tool.get_schema() for tool in self.tools.values()]
    
    def get_tools_by_category(self, category: str) -> List[BaseTool]:
        """Get tools by category."""
        return [tool for tool in self.tools.values() if tool.metadata.category == category]
    
    async def execute_tool(self, name: str, **kwargs) -> ToolResult:
        """Execute a tool by name."""
        tool = self.get_tool(name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{name}' not found"
            )
        
        if not tool.validate_params(**kwargs):
            return ToolResult(
                success=False,
                error="Invalid parameters"
            )
        
        try:
            result = await tool.execute(**kwargs)
            logger.info(f"Executed tool {name}: {'success' if result.success else 'failed'}")
            return result
        except Exception as e:
            logger.error(f"Tool {name} execution failed: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )
    
    def discover_plugins(self):
        """Discover and load plugins from the plugins directory."""
        if not self.plugins_dir.exists():
            self.plugins_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created plugins directory: {self.plugins_dir}")
            return
        
        for plugin_file in self.plugins_dir.glob("*.py"):
            if plugin_file.name.startswith("__"):
                continue
            
            try:
                self._load_plugin_file(plugin_file)
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_file}: {e}")
    
    def _load_plugin_file(self, plugin_file: Path):
        """Load a plugin from a file."""
        import importlib.util
        
        module_name = plugin_file.stem
        spec = importlib.util.spec_from_file_location(module_name, plugin_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Look for tool classes in the module
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, BaseTool) and 
                obj != BaseTool):
                
                tool_instance = obj()
                self.register_tool(tool_instance)
                logger.info(f"Loaded plugin tool: {tool_instance.metadata.name}")


# Global plugin manager instance
plugin_manager = PluginManager()