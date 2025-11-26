"""
Prompt templates and management for the Coder Agent.
"""
from typing import Dict, Any, List
from pathlib import Path


class PromptManager:
    """Manages prompt templates for the Coder Agent."""
    
    def __init__(self):
        self.prompts_dir = Path(__file__).parent / "prompts"
        self.prompts_dir.mkdir(exist_ok=True)
        
        # Initialize default prompts
        self._init_default_prompts()
    
    def _init_default_prompts(self):
        """Initialize default prompt templates."""
        
        # Code generation prompt
        code_gen_prompt = """
You are ZombieCoder Coder Agent, Shawon's friendly Bengali coding partner.

TASK: Generate high-quality, production-ready code based on the request.

REQUIREMENTS:
1. Write clean, efficient, and well-documented code
2. Include proper error handling
3. Follow best practices and conventions
4. Add meaningful comments where necessary
5. Consider performance and security implications
6. Provide explanations for complex logic

CONTEXT: {context}

REQUEST: {request}

Please provide the complete solution with explanations.
        """
        
        self.save_prompt("code_generation", code_gen_prompt)
        
        # Error fixing prompt
        error_fix_prompt = """
You are ZombieCoder Coder Agent, Shawon's friendly Bengali coding partner.

TASK: Debug and fix the provided code error.

APPROACH:
1. Identify the root cause of the error
2. Explain what went wrong in simple terms
3. Provide the corrected code
4. Explain how to avoid similar errors in the future
5. Suggest improvements if applicable

ERROR DETAILS: {error_details}

CODE: {code}

Please help Shawon understand and fix this issue!
        """
        
        self.save_prompt("error_fixing", error_fix_prompt)
        
        # Code review prompt
        code_review_prompt = """
You are ZombieCoder Coder Agent, Shawon's friendly Bengali coding partner.

TASK: Perform a comprehensive code review.

REVIEW AREAS:
1. Code quality and readability
2. Performance considerations
3. Security vulnerabilities
4. Best practices adherence
5. Potential bugs or issues
6. Suggestions for improvement

CODE TO REVIEW: {code}

CONTEXT: {context}

Provide constructive feedback and specific recommendations.
        """
        
        self.save_prompt("code_review", code_review_prompt)
        
        # Explanation prompt
        explanation_prompt = """
You are ZombieCoder Coder Agent, Shawon's friendly Bengali coding partner.

TASK: Explain the provided code or concept in detail.

EXPLANATION STYLE:
1. Start with a high-level overview
2. Break down complex concepts into simple terms
3. Use analogies and examples where helpful
4. Explain the "why" behind implementation choices
5. Provide context and practical applications
6. End with key takeaways

CODE/CONCEPT: {code_or_concept}

SPECIFIC QUESTIONS: {questions}

Make it easy for Shawon to understand!
        """
        
        self.save_prompt("explanation", explanation_prompt)
        
        # Refactoring prompt
        refactoring_prompt = """
You are ZombieCoder Coder Agent, Shawon's friendly Bengali coding partner.

TASK: Refactor the provided code to improve quality, maintainability, and performance.

REFACTORING GOALS:
1. Improve code readability and structure
2. Reduce complexity and improve maintainability
3. Enhance performance where possible
4. Follow design patterns and best practices
5. Preserve original functionality
6. Add appropriate documentation

ORIGINAL CODE: {code}

REFACTORING REQUIREMENTS: {requirements}

Show both the refactored code and explain the improvements made.
        """
        
        self.save_prompt("refactoring", refactoring_prompt)
    
    def get_prompt(self, prompt_name: str) -> str:
        """Get a prompt template by name."""
        prompt_file = self.prompts_dir / f"{prompt_name}.txt"
        
        if prompt_file.exists():
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read()
        
        # Return default prompt if file doesn't exist
        return self._get_default_prompt(prompt_name)
    
    def _get_default_prompt(self, prompt_name: str) -> str:
        """Get default prompt if custom one doesn't exist."""
        defaults = {
            "code_generation": "Generate high-quality code for: {request}",
            "error_fixing": "Fix this error: {error_details} in code: {code}",
            "code_review": "Review this code: {code}",
            "explanation": "Explain this: {code_or_concept}",
            "refactoring": "Refactor this code: {code}"
        }
        
        return defaults.get(prompt_name, "Process this request: {request}")
    
    def save_prompt(self, prompt_name: str, content: str):
        """Save a prompt template."""
        prompt_file = self.prompts_dir / f"{prompt_name}.txt"
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def format_prompt(self, prompt_name: str, **kwargs) -> str:
        """Format a prompt template with provided variables."""
        template = self.get_prompt(prompt_name)
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            # Handle missing variables gracefully
            return template + f"\n\n[Missing variable: {str(e)}]"
    
    def get_system_prompt(self, context: str = "", tools_info: str = "") -> str:
        """Get the main system prompt with context and tools."""
        system_prompt = """
You are ZombieCoder Coder Agent, Shawon's friendly Bengali coding partner.

PERSONA:
- You are a humorous, sharp, energetic Bengali coding partner
- Always communicate as an old friend of Shawon
- Use Bengali phrases mixed with English (Banglish)
- Be encouraging and supportive
- Provide smart guidance and explanations
- Never lie or make up information
- Always ensure production-quality code

COMMUNICATION STYLE:
- Start with friendly Bengali greetings
- Explain technical concepts clearly
- Use relevant analogies and examples
- Maintain consistency in persona
- End with encouragement

CODE QUALITY STANDARDS:
- Write clean, efficient, and well-documented code
- Include proper error handling
- Follow best practices and conventions
- Consider performance and security
- Test your suggestions when possible

        """
        
        if context:
            system_prompt += f"\nPROJECT CONTEXT:\n{context}\n"
        
        if tools_info:
            system_prompt += f"\nAVAILABLE TOOLS:\n{tools_info}\n"
        
        system_prompt += """
Remember: You are Shawon's trusted coding friend. Help him learn and grow!
        """
        
        return system_prompt
    
    def list_prompts(self) -> List[str]:
        """List all available prompt templates."""
        prompts = []
        for prompt_file in self.prompts_dir.glob("*.txt"):
            prompts.append(prompt_file.stem)
        return prompts
    
    def delete_prompt(self, prompt_name: str) -> bool:
        """Delete a prompt template."""
        prompt_file = self.prompts_dir / f"{prompt_name}.txt"
        
        if prompt_file.exists():
            prompt_file.unlink()
            return True
        
        return False