#!/usr/bin/env python3
"""
AI Coding Agent Pro - Advanced Interactive CLI
Features: Watch mode, batch processing, interactive mode, git integration
"""

import os
import sys
import time
import argparse
from pathlib import Path
from typing import List, Dict, Optional
import json
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import subprocess

load_dotenv()


class ColorOutput:
    """Terminal color output helper"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    
    @staticmethod
    def success(msg): return f"{ColorOutput.GREEN}✅ {msg}{ColorOutput.END}"
    
    @staticmethod
    def error(msg): return f"{ColorOutput.FAIL}❌ {msg}{ColorOutput.END}"
    
    @staticmethod
    def info(msg): return f"{ColorOutput.CYAN}ℹ️  {msg}{ColorOutput.END}"
    
    @staticmethod
    def warning(msg): return f"{ColorOutput.WARNING}⚠️  {msg}{ColorOutput.END}"
    
    @staticmethod
    def agent(msg): return f"{ColorOutput.BLUE}🤖 {msg}{ColorOutput.END}"


class AdvancedAIAgent:
    """Enhanced AI agent with caching and streaming support"""
    
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.cache = {}
    
    def analyze(self, code: str, context: str = "", stream: bool = False) -> str:
        """Analyze code with optional streaming"""
        cache_key = hash(code + context)
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            if stream:
                return self._analyze_stream(code, context)
            else:
                response = self.client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": f"{context}\n\n```python\n{code}\n```"}
                    ],
                    temperature=0.3
                )
                result = response.choices[0].message.content
                self.cache[cache_key] = result
                return result
        except Exception as e:
            return f"Error in {self.name}: {str(e)}"
    
    def _analyze_stream(self, code: str, context: str) -> str:
        """Stream analysis results in real-time"""
        try:
            stream = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"{context}\n\n```python\n{code}\n```"}
                ],
                temperature=0.3,
                stream=True
            )
            
            result = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(content, end='', flush=True)
                    result += content
            print()  # New line after streaming
            return result
        except Exception as e:
            return f"Error streaming from {self.name}: {str(e)}"


class AdvancedAgentSystem:
    """Enhanced agent system with batch processing and watch mode"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self._init_agents()
        self.results_dir = Path("agent_results")
        self.results_dir.mkdir(exist_ok=True)
    
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration from file or use defaults"""
        default_config = {
            "model": "gpt-4-turbo-preview",
            "temperature": 0.3,
            "ignore_patterns": ["*.pyc", "__pycache__", ".git", "venv", "node_modules"],
            "auto_fix": False,
            "create_backup": True
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                return {**default_config, **user_config}
        
        return default_config
    
    def _init_agents(self):
        """Initialize all specialized agents"""
        self.agents = {
            'review': AdvancedAIAgent(
                "Code Reviewer",
                """You are an expert code reviewer specializing in Python and Flask.
Focus on:
- Security vulnerabilities (OWASP Top 10)
- SQL injection, XSS, CSRF
- Authentication/authorization flaws
- Race conditions
- Error handling gaps
- Performance bottlenecks
- Code quality and maintainability

Provide severity ratings (CRITICAL/HIGH/MEDIUM/LOW) and specific fixes."""
            ),
            'docs': AdvancedAIAgent(
                "Documentation Generator",
                """You are an expert technical writer.
Generate comprehensive documentation:
- Module/class/function docstrings (Google style)
- API endpoint documentation
- Usage examples
- Configuration guides
- README sections

Be clear, concise, and developer-friendly."""
            ),
            'tests': AdvancedAIAgent(
                "Test Generator",
                """You are an expert test engineer.
Generate pytest test cases:
- Unit tests with 100% coverage goal
- Edge cases and boundary conditions
- Security tests (injection, auth bypass)
- Integration tests
- Performance tests
- Proper fixtures and mocks

Follow pytest best practices."""
            ),
            'refactor': AdvancedAIAgent(
                "Refactoring Advisor",
                """You are an expert software architect.
Suggest refactorings:
- SOLID principles violations
- Design pattern opportunities
- Code duplication (DRY)
- Complex conditionals
- God classes/functions
- Poor naming
- Missing abstractions

Provide before/after examples."""
            ),
            'security': AdvancedAIAgent(
                "Security Auditor",
                """You are a security expert specializing in web application security.
Audit for:
- OWASP Top 10 vulnerabilities
- Insecure dependencies
- Hardcoded secrets
- Weak crypto/hashing
- Missing security headers
- Rate limiting gaps
- Input validation issues
- Privilege escalation vectors

Provide exploit scenarios and fixes."""
            ),
            'performance': AdvancedAIAgent(
                "Performance Analyzer",
                """You are a performance optimization expert.
Analyze for:
- N+1 queries
- Missing indexes
- Memory leaks
- Inefficient algorithms
- Unnecessary computations
- Blocking I/O
- Missing caching
- Database query optimization

Provide benchmarks and optimized code."""
            )
        }
    
    def read_file(self, filepath: str) -> str:
        """Read file contents"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    def write_file(self, filepath: str, content: str):
        """Write content to file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def backup_file(self, filepath: str):
        """Create backup of file before modification"""
        if self.config['create_backup']:
            backup_path = f"{filepath}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            content = self.read_file(filepath)
            self.write_file(backup_path, content)
            print(ColorOutput.info(f"Backup created: {backup_path}"))
    
    def scan_directory(self, directory: str, pattern: str = "*.py") -> List[Path]:
        """Scan directory for files matching pattern"""
        path = Path(directory)
        ignore_patterns = self.config['ignore_patterns']
        
        files = []
        for file in path.rglob(pattern):
            # Skip ignored patterns
            if any(ignored in str(file) for ignored in ignore_patterns):
                continue
            files.append(file)
        
        return files
    
    def run_agent(self, agent_name: str, filepath: str, stream: bool = False) -> str:
        """Run specific agent on a file"""
        if agent_name not in self.agents:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        print(ColorOutput.agent(f"Running {self.agents[agent_name].name}..."))
        code = self.read_file(filepath)
        return self.agents[agent_name].analyze(code, stream=stream)
    
    def batch_process(self, directory: str, agents: List[str]):
        """Process all Python files in directory with specified agents"""
        files = self.scan_directory(directory)
        
        if not files:
            print(ColorOutput.warning(f"No Python files found in {directory}"))
            return
        
        print(ColorOutput.info(f"Found {len(files)} files to process"))
        
        for i, file in enumerate(files, 1):
            print(f"\n{'='*80}")
            print(ColorOutput.info(f"Processing [{i}/{len(files)}]: {file}"))
            print('='*80)
            
            report = f"# Analysis Report: {file.name}\n\n"
            report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            for agent_name in agents:
                result = self.run_agent(agent_name, str(file))
                report += f"## {self.agents[agent_name].name}\n\n{result}\n\n---\n\n"
            
            # Save report
            report_file = self.results_dir / f"{file.stem}_report.md"
            self.write_file(str(report_file), report)
            print(ColorOutput.success(f"Report saved: {report_file}"))
    
    def watch_mode(self, filepath: str, agents: List[str], interval: int = 5):
        """Watch file for changes and re-run agents"""
        print(ColorOutput.info(f"Watching {filepath} for changes (interval: {interval}s)"))
        print("Press Ctrl+C to stop\n")
        
        last_mtime = os.path.getmtime(filepath)
        
        try:
            while True:
                time.sleep(interval)
                current_mtime = os.path.getmtime(filepath)
                
                if current_mtime != last_mtime:
                    print(f"\n{'='*80}")
                    print(ColorOutput.info(f"Change detected in {filepath}"))
                    print('='*80 + "\n")
                    
                    for agent_name in agents:
                        result = self.run_agent(agent_name, filepath, stream=True)
                        print("\n")
                    
                    last_mtime = current_mtime
        
        except KeyboardInterrupt:
            print(ColorOutput.info("\nStopped watching"))
    
    def interactive_mode(self):
        """Interactive shell for running agents"""
        print(ColorOutput.info("AI Coding Agent - Interactive Mode"))
        print("Commands: review, docs, tests, refactor, security, performance, quit")
        print("Type 'help' for more information\n")
        
        while True:
            try:
                command = input(ColorOutput.BLUE + "agent> " + ColorOutput.END).strip()
                
                if not command:
                    continue
                
                if command == 'quit' or command == 'exit':
                    print(ColorOutput.info("Goodbye!"))
                    break
                
                if command == 'help':
                    self._print_help()
                    continue
                
                parts = command.split()
                agent_name = parts[0]
                
                if agent_name not in self.agents:
                    print(ColorOutput.error(f"Unknown agent: {agent_name}"))
                    continue
                
                if len(parts) < 2:
                    filepath = input("  File path: ").strip()
                else:
                    filepath = parts[1]
                
                if not Path(filepath).exists():
                    print(ColorOutput.error(f"File not found: {filepath}"))
                    continue
                
                result = self.run_agent(agent_name, filepath, stream=True)
                print()
                
                save = input("  Save report? (y/n): ").strip().lower()
                if save == 'y':
                    report_file = self.results_dir / f"{Path(filepath).stem}_{agent_name}_report.md"
                    self.write_file(str(report_file), result)
                    print(ColorOutput.success(f"Saved to {report_file}"))
            
            except KeyboardInterrupt:
                print(ColorOutput.info("\nUse 'quit' to exit"))
            except Exception as e:
                print(ColorOutput.error(f"Error: {str(e)}"))
    
    def _print_help(self):
        """Print help information"""
        help_text = """
Available Commands:
  review <file>      - Run code review and bug detection
  docs <file>        - Generate documentation
  tests <file>       - Generate test cases
  refactor <file>    - Get refactoring suggestions
  security <file>    - Run security audit
  performance <file> - Analyze performance issues
  quit/exit          - Exit interactive mode
  help               - Show this help message

Examples:
  agent> review myapp.py
  agent> tests src/models.py
  agent> security auth.py
        """
        print(help_text)
    
    def git_integration(self, commit: bool = False):
        """Analyze git changes and optionally commit analysis"""
        try:
            # Get changed files
            result = subprocess.run(
                ['git', 'diff', '--name-only'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(ColorOutput.error("Not a git repository"))
                return
            
            changed_files = [f for f in result.stdout.split('\n') if f.endswith('.py')]
            
            if not changed_files:
                print(ColorOutput.info("No Python files changed"))
                return
            
            print(ColorOutput.info(f"Found {len(changed_files)} changed Python files"))
            
            for file in changed_files:
                print(f"\n{'='*80}")
                print(ColorOutput.info(f"Analyzing: {file}"))
                print('='*80)
                
                # Run review agent on changed files
                result = self.run_agent('review', file)
                print(result)
            
            if commit:
                # Create analysis report and commit
                report = f"Code analysis for commit {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                # Add commit logic here
                print(ColorOutput.info("Analysis complete - review before committing"))
        
        except Exception as e:
            print(ColorOutput.error(f"Git integration error: {str(e)}"))


def main():
    parser = argparse.ArgumentParser(
        description='AI Coding Agent Pro - Advanced Interactive CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python ai_coding_agent_pro.py -i
  
  # Review a specific file
  python ai_coding_agent_pro.py review myapp.py
  
  # Batch process directory
  python ai_coding_agent_pro.py batch src/ --agents review security
  
  # Watch file for changes
  python ai_coding_agent_pro.py watch myapp.py --agents review tests
  
  # Analyze git changes
  python ai_coding_agent_pro.py git-check
  
  # Run full analysis
  python ai_coding_agent_pro.py full myapp.py -o report.md
        """
    )
    
    parser.add_argument('command', nargs='?', help='Command to run')
    parser.add_argument('target', nargs='?', help='File or directory target')
    
    parser.add_argument('-i', '--interactive', action='store_true',
                       help='Start interactive mode')
    parser.add_argument('-o', '--output', help='Output file')
    parser.add_argument('-c', '--config', help='Config file path')
    parser.add_argument('--agents', nargs='+', 
                       default=['review', 'security'],
                       help='Agents to run')
    parser.add_argument('--stream', action='store_true',
                       help='Stream output in real-time')
    parser.add_argument('--interval', type=int, default=5,
                       help='Watch mode interval (seconds)')
    
    args = parser.parse_args()
    
    if not os.getenv('OPENAI_API_KEY'):
        print(ColorOutput.error("OPENAI_API_KEY environment variable not set"))
        sys.exit(1)
    
    system = AdvancedAgentSystem(args.config)
    
    try:
        if args.interactive:
            system.interactive_mode()
        
        elif args.command == 'batch':
            if not args.target:
                print(ColorOutput.error("Directory required for batch mode"))
                sys.exit(1)
            system.batch_process(args.target, args.agents)
        
        elif args.command == 'watch':
            if not args.target:
                print(ColorOutput.error("File required for watch mode"))
                sys.exit(1)
            system.watch_mode(args.target, args.agents, args.interval)
        
        elif args.command == 'git-check':
            system.git_integration()
        
        elif args.command == 'full':
            if not args.target:
                print(ColorOutput.error("File required"))
                sys.exit(1)
            
            all_agents = ['review', 'docs', 'tests', 'refactor', 'security', 'performance']
            report = f"# Complete Analysis: {args.target}\n\n"
            
            for agent_name in all_agents:
                print(ColorOutput.agent(f"Running {system.agents[agent_name].name}..."))
                result = system.run_agent(agent_name, args.target)
                report += f"## {system.agents[agent_name].name}\n\n{result}\n\n---\n\n"
            
            if args.output:
                system.write_file(args.output, report)
                print(ColorOutput.success(f"Report saved: {args.output}"))
            else:
                print(report)
        
        elif args.command in system.agents:
            if not args.target:
                print(ColorOutput.error("File required"))
                sys.exit(1)
            
            result = system.run_agent(args.command, args.target, args.stream)
            
            if args.output:
                system.write_file(args.output, result)
                print(ColorOutput.success(f"Report saved: {args.output}"))
            else:
                if not args.stream:  # Don't print again if streaming
                    print(result)
        
        else:
            parser.print_help()
    
    except Exception as e:
        print(ColorOutput.error(f"Error: {str(e)}"))
        sys.exit(1)


if __name__ == '__main__':
    main()
