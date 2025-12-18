#!/usr/bin/env python3
"""
AI Coding Agent - CLI tool for automated code assistance
Similar to Claude Code, works directly on files in your terminal
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Optional
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class AIAgent:
    """Base class for all AI coding agents"""
    
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def analyze(self, code: str, context: str = "") -> str:
        """Analyze code using the agent's specialized knowledge"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"{context}\n\n```python\n{code}\n```"}
                ],
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error in {self.name}: {str(e)}"


class CodeReviewAgent(AIAgent):
    """Agent specialized in code review and bug detection"""
    
    def __init__(self):
        system_prompt = """You are an expert code reviewer specializing in Python.
Analyze the provided code for:
- Bugs and logic errors
- Security vulnerabilities (SQL injection, XSS, CSRF issues)
- Performance issues
- Code smells and anti-patterns
- Best practice violations
- Race conditions and concurrency issues
- Error handling gaps
- Input validation issues

Provide specific line numbers and actionable recommendations.
Format output as:
## Critical Issues
## Security Concerns  
## Performance Issues
## Best Practice Suggestions
## Code Quality"""
        super().__init__("Code Reviewer", system_prompt)


class DocumentationAgent(AIAgent):
    """Agent specialized in generating documentation"""
    
    def __init__(self):
        system_prompt = """You are an expert technical writer specializing in Python documentation.
Generate comprehensive documentation including:
- Module/class docstrings in Google style
- Function/method docstrings with Args, Returns, Raises
- Inline comments for complex logic
- README sections
- API documentation
- Usage examples

Follow PEP 257 and Google Python Style Guide.
Make documentation clear, concise, and useful."""
        super().__init__("Documentation Generator", system_prompt)


class TestGeneratorAgent(AIAgent):
    """Agent specialized in generating test cases"""
    
    def __init__(self):
        system_prompt = """You are an expert test engineer specializing in Python testing.
Generate comprehensive test cases using pytest including:
- Unit tests for all functions/methods
- Edge cases and boundary conditions
- Error condition tests
- Mock/patch external dependencies
- Parametrized tests where appropriate
- Integration tests
- Security test cases (injection, auth bypass, etc.)
- Performance tests for critical paths

Follow pytest best practices and provide fixtures where needed."""
        super().__init__("Test Generator", system_prompt)


class RefactoringAgent(AIAgent):
    """Agent specialized in code refactoring suggestions"""
    
    def __init__(self):
        system_prompt = """You are an expert software engineer specializing in Python refactoring.
Analyze code and suggest refactorings for:
- Extract method/class opportunities
- Remove code duplication (DRY principle)
- Simplify complex conditionals
- Improve naming
- Apply design patterns
- Separate concerns
- Improve modularity
- Enhance readability
- Type hints and annotations
- Modern Python idioms (f-strings, comprehensions, etc.)

Provide before/after code examples with explanations."""
        super().__init__("Refactoring Advisor", system_prompt)


class BoilerplateAgent(AIAgent):
    """Agent specialized in generating boilerplate code"""
    
    def __init__(self):
        system_prompt = """You are an expert Python developer specializing in generating boilerplate code.
Generate production-ready boilerplate for:
- Flask routes with proper error handling
- Database models (SQLAlchemy/raw SQL)
- API endpoints (REST/GraphQL)
- Authentication/authorization decorators
- Validation schemas (Pydantic/marshmallow)
- CLI commands (argparse/click)
- Configuration management
- Logging setup
- Testing fixtures
- Docker/deployment configs

Include proper type hints, docstrings, and error handling."""
        super().__init__("Boilerplate Generator", system_prompt)


class AgentSystem:
    """Main system that coordinates all AI agents"""
    
    def __init__(self):
        self.agents = {
            'review': CodeReviewAgent(),
            'docs': DocumentationAgent(),
            'tests': TestGeneratorAgent(),
            'refactor': RefactoringAgent(),
            'boilerplate': BoilerplateAgent()
        }
    
    def read_file(self, filepath: str) -> str:
        """Read file contents"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise Exception(f"Error reading file {filepath}: {str(e)}")
    
    def write_file(self, filepath: str, content: str):
        """Write content to file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Written to {filepath}")
        except Exception as e:
            raise Exception(f"Error writing file {filepath}: {str(e)}")
    
    def run_agent(self, agent_name: str, filepath: str, context: str = "") -> str:
        """Run a specific agent on a file"""
        if agent_name not in self.agents:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        code = self.read_file(filepath)
        agent = self.agents[agent_name]
        
        print(f"\n🤖 Running {agent.name}...")
        result = agent.analyze(code, context)
        return result
    
    def run_all_agents(self, filepath: str) -> Dict[str, str]:
        """Run all agents on a file"""
        results = {}
        for agent_name, agent in self.agents.items():
            print(f"\n🤖 Running {agent.name}...")
            code = self.read_file(filepath)
            results[agent_name] = agent.analyze(code)
        return results


def main():
    parser = argparse.ArgumentParser(
        description='AI Coding Agent - Automated code assistance CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Review a file for bugs and security issues
  python ai_coding_agent.py review myapp.py
  
  # Generate documentation for a file
  python ai_coding_agent.py docs myapp.py -o myapp_docs.md
  
  # Generate test cases
  python ai_coding_agent.py tests myapp.py -o test_myapp.py
  
  # Get refactoring suggestions
  python ai_coding_agent.py refactor myapp.py
  
  # Generate boilerplate code
  python ai_coding_agent.py boilerplate --type flask-route --name "user_profile"
  
  # Run all agents
  python ai_coding_agent.py all myapp.py -o analysis_report.md
        """
    )
    
    parser.add_argument(
        'command',
        choices=['review', 'docs', 'tests', 'refactor', 'boilerplate', 'all'],
        help='Agent command to run'
    )
    
    parser.add_argument(
        'file',
        nargs='?',
        help='File to analyze (not needed for boilerplate)'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output file (default: print to stdout)'
    )
    
    parser.add_argument(
        '-c', '--context',
        default='',
        help='Additional context for the agent'
    )
    
    parser.add_argument(
        '--type',
        help='Type of boilerplate to generate (flask-route, model, api-endpoint, etc.)'
    )
    
    parser.add_argument(
        '--name',
        help='Name for the boilerplate component'
    )
    
    args = parser.parse_args()
    
    # Check if OpenAI API key is set
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Set it with: export OPENAI_API_KEY='your-key-here'")
        sys.exit(1)
    
    system = AgentSystem()
    
    try:
        if args.command == 'boilerplate':
            # Generate boilerplate code
            if not args.type or not args.name:
                print("❌ Error: --type and --name required for boilerplate generation")
                sys.exit(1)
            
            context = f"Generate {args.type} boilerplate for: {args.name}"
            result = system.agents['boilerplate'].analyze("", context)
        
        elif args.command == 'all':
            # Run all agents
            if not args.file:
                print("❌ Error: file argument required")
                sys.exit(1)
            
            results = system.run_all_agents(args.file)
            
            # Combine all results
            report = f"# AI Code Analysis Report: {args.file}\n\n"
            report += f"Generated: {Path(args.file).name}\n\n"
            
            section_titles = {
                'review': '## 🔍 Code Review & Bug Detection',
                'docs': '## 📚 Documentation Generation',
                'tests': '## 🧪 Test Case Generation',
                'refactor': '## ♻️ Refactoring Suggestions',
                'boilerplate': '## 🏗️ Boilerplate Patterns'
            }
            
            for agent_name, agent_result in results.items():
                report += f"\n{section_titles[agent_name]}\n\n"
                report += agent_result + "\n\n"
                report += "---\n"
            
            result = report
        
        else:
            # Run specific agent
            if not args.file:
                print("❌ Error: file argument required")
                sys.exit(1)
            
            result = system.run_agent(args.command, args.file, args.context)
        
        # Output results
        if args.output:
            system.write_file(args.output, result)
        else:
            print("\n" + "="*80)
            print(result)
            print("="*80)
        
        print("\n✅ Done!")
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
