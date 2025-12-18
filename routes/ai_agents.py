"""AI Agent routes - Smart preprocessing, chunking, analysis, metadata suggestions"""

from flask import Blueprint, request, jsonify, session
from functools import wraps

ai_agents_bp = Blueprint('ai_agents', __name__)

# Dependencies
agent_system = None

def init_ai_agents(agents):
    """Initialize AI agents blueprint with dependencies"""
    global agent_system
    agent_system = agents

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@ai_agents_bp.route('/api/agent/preprocess', methods=['POST'])
@login_required
def agent_preprocess():
    """Preprocess text using AI agent"""
    try:
        data = request.get_json()
        text = data.get('text', '')

        if not agent_system:
            return jsonify({'error': 'AI agents not initialized'}), 500

        processed_text = agent_system.preprocess_text(text)

        return jsonify({
            'success': True,
            'original_text': text,
            'processed_text': processed_text,
            'original_length': len(text),
            'processed_length': len(processed_text)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_agents_bp.route('/api/agent/suggest-metadata', methods=['POST'])
@login_required
def agent_suggest_metadata():
    """Get AI-powered metadata suggestions"""
    try:
        data = request.get_json()
        text = data.get('text', '')

        if not agent_system:
            return jsonify({'error': 'AI agents not initialized'}), 500

        suggestions = agent_system.suggest_metadata(text)

        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_agents_bp.route('/api/agent/analyze', methods=['POST'])
@login_required
def agent_analyze():
    """Analyze text quality for TTS"""
    try:
        data = request.get_json()
        text = data.get('text', '')

        if not agent_system:
            return jsonify({'error': 'AI agents not initialized'}), 500

        analysis = agent_system.analyze_quality(text)

        return jsonify({
            'success': True,
            'analysis': analysis
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_agents_bp.route('/api/agent/smart-chunk', methods=['POST'])
@login_required
def agent_smart_chunk():
    """Smart chunk long text"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        max_chars = data.get('max_chars', 4000)

        if not agent_system:
            return jsonify({'error': 'AI agents not initialized'}), 500

        chunks = agent_system.smart_chunk(text, max_chars=max_chars)

        return jsonify({
            'success': True,
            'chunks': chunks,
            'total_chunks': len(chunks)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
