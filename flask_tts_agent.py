#!/usr/bin/env python3
"""
Flask TTS App Specialized Agent
Custom agent that understands your VoiceVerse TTS application
"""

import os
import sys
from pathlib import Path
from typing import Dict, List
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class FlaskTTSAgent:
    """Specialized agent for Flask TTS applications"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.context = self._load_app_context()
    
    def _load_app_context(self) -> str:
        """Load application-specific context"""
        return """
You are analyzing a Flask-based Text-to-Speech (TTS) application called VoiceVerse with:

TECH STACK:
- Flask web framework
- OpenAI TTS API
- SQLite database (via custom Database class)
- Security: Flask-WTF CSRF protection, Flask-Limiter for rate limiting
- Authentication: Session-based with password hashing
- File handling: DOCX and PDF support (python-docx, PyPDF2)
- Monitoring: Custom metrics collector and log analyzer
- Security logging and alerts system

KEY FEATURES:
- User authentication and authorization
- Text-to-speech conversion with multiple voices
- File upload and processing
- Audio history management
- Security audit logging
- Rate limiting and lockout protection
- Admin dashboard with monitoring
- HTTPS/TLS support

SECURITY FOCUS AREAS:
- SQL injection prevention
- XSS protection
- CSRF tokens
- Session security
- Rate limiting
- Input validation
- Secure file handling
- IP address hashing for privacy
- Security headers (CSP, HSTS, X-Frame-Options)

COMMON PATTERNS:
- @login_required decorator for protected routes
- Security event logging via log_security_event()
- Database queries using custom db.execute()
- File ownership validation
- Error handling with try/except and user feedback
        """
    
    def analyze_route_security(self, code: str) -> str:
        """Analyze Flask route for security issues"""
        prompt = f"""{self.context}

Analyze this Flask route for security vulnerabilities:

```python
{code}
```

Check for:
1. Missing @login_required decorator
2. Missing CSRF protection
3. Missing rate limiting
4. SQL injection vulnerabilities
5. XSS vulnerabilities
6. Missing input validation
7. Improper error handling
8. Missing security logging
9. File upload vulnerabilities
10. Authorization checks

Provide specific fixes with code examples."""
        
        return self._query_openai(prompt)
    
    def generate_flask_tests(self, code: str) -> str:
        """Generate tests specific to Flask routes"""
        prompt = f"""{self.context}

Generate comprehensive pytest test cases for this Flask route:

```python
{code}
```

Include:
1. Authenticated user tests
2. Unauthenticated user tests (should redirect)
3. CSRF token tests
4. Rate limiting tests
5. Input validation tests
6. SQL injection attempt tests
7. XSS attempt tests
8. File upload tests (if applicable)
9. Error condition tests
10. Security logging verification tests

Use Flask test client and pytest fixtures."""
        
        return self._query_openai(prompt)
    
    def suggest_flask_improvements(self, code: str) -> str:
        """Suggest Flask-specific improvements"""
        prompt = f"""{self.context}

Analyze this Flask code and suggest improvements:

```python
{code}
```

Focus on:
1. Flask best practices
2. Security enhancements
3. Performance optimization
4. Error handling
5. Code organization
6. Database query optimization
7. Session management
8. Logging and monitoring
9. Type hints and documentation
10. Testing coverage

Provide before/after code examples."""
        
        return self._query_openai(prompt)
    
    def generate_route_boilerplate(self, route_spec: Dict) -> str:
        """Generate Flask route boilerplate"""
        prompt = f"""{self.context}

Generate a complete Flask route with full security based on:

Route: {route_spec.get('path', '/api/endpoint')}
Method: {route_spec.get('method', 'POST')}
Purpose: {route_spec.get('purpose', 'API endpoint')}
Auth Required: {route_spec.get('auth', True)}
Rate Limit: {route_spec.get('rate_limit', '10 per minute')}

Include:
1. @login_required decorator (if auth required)
2. @limiter.limit() decorator
3. CSRF protection
4. Input validation
5. Database interaction (if needed)
6. Error handling
7. Security logging
8. Success/error responses
9. Docstring
10. Type hints

Follow the VoiceVerse coding style."""
        
        return self._query_openai(prompt)
    
    def audit_database_queries(self, code: str) -> str:
        """Audit database queries for SQL injection and performance"""
        prompt = f"""{self.context}

Audit database queries in this code:

```python
{code}
```

Check for:
1. SQL injection vulnerabilities
2. Missing parameterized queries
3. N+1 query problems
4. Missing indexes
5. Inefficient queries
6. Missing error handling
7. Transaction management
8. Connection leaks

Provide safe alternatives and performance improvements."""
        
        return self._query_openai(prompt)
    
    def analyze_auth_flow(self, code: str) -> str:
        """Analyze authentication and authorization logic"""
        prompt = f"""{self.context}

Analyze authentication/authorization in this code:

```python
{code}
```

Check for:
1. Password storage (should use hashing)
2. Session management security
3. Missing authorization checks
4. Privilege escalation vulnerabilities
5. Brute force protection
6. Account lockout mechanism
7. Security logging
8. Token/session expiration
9. Secure cookie settings
10. Remember me functionality

Provide security recommendations."""
        
        return self._query_openai(prompt)
    
    def _query_openai(self, prompt: str) -> str:
        """Query OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert Flask security consultant specializing in web application security."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"


def main():
    """CLI interface for Flask TTS Agent"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Flask TTS Application Specialized Agent')
    parser.add_argument('command', choices=[
        'route-security', 'tests', 'improvements', 
        'boilerplate', 'db-audit', 'auth-audit'
    ])
    parser.add_argument('file', nargs='?', help='File to analyze')
    parser.add_argument('-o', '--output', help='Output file')
    
    # Boilerplate generation options
    parser.add_argument('--path', help='Route path (for boilerplate)')
    parser.add_argument('--method', default='POST', help='HTTP method')
    parser.add_argument('--purpose', help='Route purpose')
    parser.add_argument('--auth', action='store_true', default=True, help='Requires authentication')
    parser.add_argument('--rate-limit', default='10 per minute', help='Rate limit')
    
    args = parser.parse_args()
    
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY not set")
        sys.exit(1)
    
    agent = FlaskTTSAgent()
    
    try:
        if args.command == 'boilerplate':
            route_spec = {
                'path': args.path or '/api/endpoint',
                'method': args.method,
                'purpose': args.purpose or 'API endpoint',
                'auth': args.auth,
                'rate_limit': args.rate_limit
            }
            result = agent.generate_route_boilerplate(route_spec)
        else:
            if not args.file:
                print("❌ Error: file argument required")
                sys.exit(1)
            
            with open(args.file, 'r') as f:
                code = f.read()
            
            if args.command == 'route-security':
                result = agent.analyze_route_security(code)
            elif args.command == 'tests':
                result = agent.generate_flask_tests(code)
            elif args.command == 'improvements':
                result = agent.suggest_flask_improvements(code)
            elif args.command == 'db-audit':
                result = agent.audit_database_queries(code)
            elif args.command == 'auth-audit':
                result = agent.analyze_auth_flow(code)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(result)
            print(f"✅ Written to {args.output}")
        else:
            print("\n" + "="*80)
            print(result)
            print("="*80)
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
