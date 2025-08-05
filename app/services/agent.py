"""
AI Agent service for handling code generation and assistance.
"""
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.core.config import settings
from app.core.memory import memory

logger = logging.getLogger(__name__)


class CodeRequest(BaseModel):
    """Request model for code generation."""
    prompt: str
    language: Optional[str] = "python"
    context: Optional[str] = None
    max_tokens: Optional[int] = None


class CodeResponse(BaseModel):
    """Response model for code generation."""
    code: str
    explanation: str
    language: str
    confidence: float


class ChatRequest(BaseModel):
    """Request model for chat interactions."""
    message: str
    context: Optional[str] = None
    use_memory: bool = True


class ChatResponse(BaseModel):
    """Response model for chat interactions."""
    response: str
    context_used: List[Dict[str, Any]]
    confidence: float


class AIAgent:
    """Main AI Agent for code generation and assistance."""
    
    def __init__(self):
        self.model_name = settings.model_name
        self.max_tokens = settings.max_tokens
        self._client = None
        
    def _get_client(self):
        """Get OpenAI client instance."""
        if self._client is None:
            if not settings.openai_api_key:
                # Return a mock client for testing purposes
                logger.warning("OpenAI API key not configured. Using mock responses.")
                return None
            
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=settings.openai_api_key)
            except ImportError:
                logger.warning("OpenAI package not available. Using mock responses.")
                return None
        
        return self._client
    
    def _build_system_prompt(self, task_type: str = "general") -> str:
        """Build system prompt based on task type."""
        base_prompt = """You are an advanced AI coding assistant. You help developers with:
- Code generation and completion
- Code review and optimization
- Debugging and troubleshooting
- Architecture and design advice
- Best practices and patterns

Always provide clear, well-commented, and functional code. Explain your reasoning and suggest improvements where appropriate."""
        
        if task_type == "code_generation":
            return base_prompt + "\n\nFocus on generating clean, efficient, and well-documented code."
        elif task_type == "debugging":
            return base_prompt + "\n\nFocus on identifying issues and providing clear debugging steps."
        elif task_type == "review":
            return base_prompt + "\n\nFocus on code quality, performance, security, and maintainability."
        
        return base_prompt
    
    def _get_relevant_context(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Get relevant context from memory."""
        try:
            return memory.search_relevant_context(query, k)
        except Exception as e:
            logger.warning(f"Failed to retrieve context from memory: {e}")
            return []
    
    def _format_context(self, context_items: List[Dict[str, Any]]) -> str:
        """Format context items for inclusion in prompt."""
        if not context_items:
            return ""
        
        formatted_context = "\n\nRelevant context from previous interactions:\n"
        for i, item in enumerate(context_items, 1):
            formatted_context += f"\n{i}. {item['document'][:500]}..."
            if 'metadata' in item and item['metadata'].get('type'):
                formatted_context += f" (Type: {item['metadata']['type']})"
        
        return formatted_context
    
    async def generate_code(self, request: CodeRequest) -> CodeResponse:
        """Generate code based on the request."""
        try:
            client = self._get_client()
            
            # Get relevant context from memory
            context_items = self._get_relevant_context(request.prompt)
            context_str = self._format_context(context_items)
            
            # Build the prompt
            full_prompt = f"Generate {request.language} code for the following request:\n\n{request.prompt}"
            
            if request.context:
                full_prompt += f"\n\nAdditional context:\n{request.context}"
            
            full_prompt += context_str
            
            # If no OpenAI client available, provide mock response
            if client is None:
                # Generate a simple mock response based on the request
                if "hello" in request.prompt.lower():
                    code = f"def hello_world():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    hello_world()"
                    explanation = "This is a simple Hello World function that prints a greeting message."
                elif "add" in request.prompt.lower() or "sum" in request.prompt.lower():
                    code = f"def add_numbers(a, b):\n    return a + b\n\nresult = add_numbers(5, 3)\nprint(f'Result: {{result}}')"
                    explanation = "This function adds two numbers and returns the result."
                else:
                    code = f"# Generated {request.language} code\n# TODO: Implement the requested functionality\npass"
                    explanation = f"This is a placeholder for {request.prompt}. Please implement the actual functionality."
            else:
                # Call OpenAI API
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self._build_system_prompt("code_generation")},
                        {"role": "user", "content": full_prompt}
                    ],
                    max_tokens=request.max_tokens or self.max_tokens,
                    temperature=0.1
                )
                
                # Parse response
                content = response.choices[0].message.content
                
                # Try to extract code and explanation
                code_blocks = []
                explanation = content
                
                # Simple code block extraction
                if "```" in content:
                    lines = content.split('\n')
                    in_code_block = False
                    current_code = []
                    
                    for line in lines:
                        if line.strip().startswith("```"):
                            if in_code_block:
                                if current_code:
                                    code_blocks.append('\n'.join(current_code))
                                current_code = []
                                in_code_block = False
                            else:
                                in_code_block = True
                        elif in_code_block:
                            current_code.append(line)
                    
                    if current_code:
                        code_blocks.append('\n'.join(current_code))
                
                # Use the first code block if available, otherwise use full content
                code = code_blocks[0] if code_blocks else content
            
            # Store in memory
            memory.add_code_context(code, request.prompt, {
                'language': request.language,
                'timestamp': 'now'  # In production, use proper timestamp
            })
            
            return CodeResponse(
                code=code,
                explanation=explanation,
                language=request.language,
                confidence=0.8  # Mock confidence score
            )
            
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            raise
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Handle chat interactions."""
        try:
            client = self._get_client()
            
            # Get relevant context from memory if requested
            context_items = []
            if request.use_memory:
                context_items = self._get_relevant_context(request.message)
            
            context_str = self._format_context(context_items)
            
            # Build the prompt
            full_prompt = request.message
            
            if request.context:
                full_prompt += f"\n\nContext: {request.context}"
            
            full_prompt += context_str
            
            # If no OpenAI client available, provide mock response
            if client is None:
                # Generate a simple mock response based on the message
                if "hello" in request.message.lower() or "hi" in request.message.lower():
                    assistant_response = "Hello! I'm your AI coding assistant. I can help you with code generation, debugging, and programming questions. How can I assist you today?"
                elif "help" in request.message.lower():
                    assistant_response = "I can help you with:\n- Code generation in various programming languages\n- Code review and optimization\n- Debugging assistance\n- Programming best practices\n- Architecture advice\n\nWhat would you like to work on?"
                elif "code" in request.message.lower():
                    assistant_response = "I'd be happy to help you with coding! Please let me know what specific programming task you need assistance with, and I'll generate the appropriate code for you."
                else:
                    assistant_response = f"I understand you're asking about: {request.message}\n\nAs an AI coding assistant, I'm here to help with programming tasks. Could you provide more details about what you'd like me to help you code or debug?"
            else:
                # Call OpenAI API
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self._build_system_prompt("general")},
                        {"role": "user", "content": full_prompt}
                    ],
                    max_tokens=self.max_tokens,
                    temperature=0.3
                )
                
                assistant_response = response.choices[0].message.content
            
            # Store conversation in memory
            memory.add_conversation(request.message, assistant_response, {
                'timestamp': 'now'  # In production, use proper timestamp
            })
            
            return ChatResponse(
                response=assistant_response,
                context_used=context_items,
                confidence=0.8  # Mock confidence score
            )
            
        except Exception as e:
            logger.error(f"Chat interaction failed: {e}")
            raise
    
    def review_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Review code and provide feedback."""
        # This is a simplified version - in production, this would use more sophisticated analysis
        feedback = {
            "overall_score": 7.5,
            "suggestions": [
                "Consider adding more comments for better readability",
                "Add error handling for edge cases",
                "Consider using type hints for better code documentation"
            ],
            "security_issues": [],
            "performance_notes": ["Code looks efficient for most use cases"],
            "style_issues": ["Follow PEP 8 guidelines for Python code"]
        }
        
        return feedback


# Global agent instance
agent = AIAgent()