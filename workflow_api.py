"""
VoiceVerse Workflow Editor API
Visual drag-and-drop workflow builder with AI agent management
"""

from flask import Blueprint, jsonify, request, session
from functools import wraps
import json
import os
from datetime import datetime
import uuid
from agent_executor import AgentExecutor, AGENT_NODE_TYPES

workflow_bp = Blueprint('workflow', __name__, url_prefix='/api/workflow')

# Initialize agent executor
agent_executor = None

def init_agent_executor(openai_client):
    """Initialize the agent executor with OpenAI client"""
    global agent_executor
    agent_executor = AgentExecutor(openai_client)

# Workflow storage directory
WORKFLOWS_DIR = 'workflows'
AGENTS_DIR = 'agents'

# Ensure directories exist
os.makedirs(WORKFLOWS_DIR, exist_ok=True)
os.makedirs(AGENTS_DIR, exist_ok=True)


def login_required_api(f):
    """API version of login_required that returns JSON"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# WORKFLOW ENDPOINTS
# ============================================================================

@workflow_bp.route('/workflows', methods=['GET'])
@login_required_api
def get_workflows():
    """Get all workflows for the current user"""
    username = session.get('username')
    user_workflows = []

    try:
        for filename in os.listdir(WORKFLOWS_DIR):
            if filename.endswith('.json'):
                filepath = os.path.join(WORKFLOWS_DIR, filename)
                with open(filepath, 'r') as f:
                    workflow = json.load(f)
                    # Filter by user
                    if workflow.get('owner') == username:
                        user_workflows.append(workflow)

        return jsonify({'workflows': user_workflows}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@workflow_bp.route('/workflows', methods=['POST'])
@login_required_api
def create_workflow():
    """Create a new workflow"""
    username = session.get('username')
    data = request.get_json()

    if not data or 'name' not in data:
        return jsonify({'error': 'Workflow name is required'}), 400

    workflow_id = str(uuid.uuid4())
    workflow = {
        'id': workflow_id,
        'name': data['name'],
        'description': data.get('description', ''),
        'owner': username,
        'nodes': data.get('nodes', []),
        'edges': data.get('edges', []),
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat(),
        'status': 'draft'
    }

    try:
        filepath = os.path.join(WORKFLOWS_DIR, f'{workflow_id}.json')
        with open(filepath, 'w') as f:
            json.dump(workflow, f, indent=2)

        return jsonify({'workflow': workflow}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@workflow_bp.route('/workflows/<workflow_id>', methods=['GET'])
@login_required_api
def get_workflow(workflow_id):
    """Get a specific workflow"""
    username = session.get('username')

    try:
        filepath = os.path.join(WORKFLOWS_DIR, f'{workflow_id}.json')
        if not os.path.exists(filepath):
            return jsonify({'error': 'Workflow not found'}), 404

        with open(filepath, 'r') as f:
            workflow = json.load(f)

        # Check ownership
        if workflow.get('owner') != username:
            return jsonify({'error': 'Unauthorized'}), 403

        return jsonify({'workflow': workflow}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@workflow_bp.route('/workflows/<workflow_id>', methods=['PUT'])
@login_required_api
def update_workflow(workflow_id):
    """Update an existing workflow"""
    username = session.get('username')
    data = request.get_json()

    try:
        filepath = os.path.join(WORKFLOWS_DIR, f'{workflow_id}.json')
        if not os.path.exists(filepath):
            return jsonify({'error': 'Workflow not found'}), 404

        with open(filepath, 'r') as f:
            workflow = json.load(f)

        # Check ownership
        if workflow.get('owner') != username:
            return jsonify({'error': 'Unauthorized'}), 403

        # Update fields
        workflow['name'] = data.get('name', workflow['name'])
        workflow['description'] = data.get('description', workflow['description'])
        workflow['nodes'] = data.get('nodes', workflow['nodes'])
        workflow['edges'] = data.get('edges', workflow['edges'])
        workflow['updated_at'] = datetime.utcnow().isoformat()

        with open(filepath, 'w') as f:
            json.dump(workflow, f, indent=2)

        return jsonify({'workflow': workflow}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@workflow_bp.route('/workflows/<workflow_id>', methods=['DELETE'])
@login_required_api
def delete_workflow(workflow_id):
    """Delete a workflow"""
    username = session.get('username')

    try:
        filepath = os.path.join(WORKFLOWS_DIR, f'{workflow_id}.json')
        if not os.path.exists(filepath):
            return jsonify({'error': 'Workflow not found'}), 404

        with open(filepath, 'r') as f:
            workflow = json.load(f)

        # Check ownership
        if workflow.get('owner') != username:
            return jsonify({'error': 'Unauthorized'}), 403

        os.remove(filepath)
        return jsonify({'message': 'Workflow deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@workflow_bp.route('/workflows/<workflow_id>/execute', methods=['POST'])
@login_required_api
def execute_workflow(workflow_id):
    """Execute a workflow"""
    username = session.get('username')
    data = request.get_json()

    try:
        filepath = os.path.join(WORKFLOWS_DIR, f'{workflow_id}.json')
        if not os.path.exists(filepath):
            return jsonify({'error': 'Workflow not found'}), 404

        with open(filepath, 'r') as f:
            workflow = json.load(f)

        # Check ownership
        if workflow.get('owner') != username:
            return jsonify({'error': 'Unauthorized'}), 403

        # Execute workflow using agent executor
        execution_start = datetime.utcnow()

        # Add inputs from request to workflow
        workflow['inputs'] = data.get('inputs', {})

        # Execute the workflow
        if agent_executor is None:
            return jsonify({'error': 'Agent executor not initialized'}), 500

        result = agent_executor.execute_workflow(workflow)

        execution_result = {
            'execution_id': str(uuid.uuid4()),
            'workflow_id': workflow_id,
            'status': result.get('status', 'completed'),
            'started_at': execution_start.isoformat(),
            'completed_at': datetime.utcnow().isoformat(),
            'inputs': data.get('inputs', {}),
            'outputs': result.get('final_output', {}),
            'node_outputs': result.get('node_outputs', {}),
            'nodes_executed': result.get('nodes_executed', 0)
        }

        return jsonify({'execution': execution_result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# AGENT ENDPOINTS
# ============================================================================

@workflow_bp.route('/agents', methods=['GET'])
@login_required_api
def get_agents():
    """Get all agents for the current user"""
    username = session.get('username')
    user_agents = []

    try:
        for filename in os.listdir(AGENTS_DIR):
            if filename.endswith('.json'):
                filepath = os.path.join(AGENTS_DIR, filename)
                with open(filepath, 'r') as f:
                    agent = json.load(f)
                    # Filter by user
                    if agent.get('owner') == username:
                        user_agents.append(agent)

        return jsonify({'agents': user_agents}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@workflow_bp.route('/agents', methods=['POST'])
@login_required_api
def create_agent():
    """Create a new agent"""
    username = session.get('username')
    data = request.get_json()

    if not data or 'name' not in data or 'type' not in data:
        return jsonify({'error': 'Agent name and type are required'}), 400

    agent_id = str(uuid.uuid4())
    agent = {
        'id': agent_id,
        'name': data['name'],
        'type': data['type'],  # 'tts', 'analysis', 'custom', etc.
        'description': data.get('description', ''),
        'owner': username,
        'config': data.get('config', {}),
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }

    try:
        filepath = os.path.join(AGENTS_DIR, f'{agent_id}.json')
        with open(filepath, 'w') as f:
            json.dump(agent, f, indent=2)

        return jsonify({'agent': agent}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@workflow_bp.route('/agents/<agent_id>', methods=['GET'])
@login_required_api
def get_agent(agent_id):
    """Get a specific agent"""
    username = session.get('username')

    try:
        filepath = os.path.join(AGENTS_DIR, f'{agent_id}.json')
        if not os.path.exists(filepath):
            return jsonify({'error': 'Agent not found'}), 404

        with open(filepath, 'r') as f:
            agent = json.load(f)

        # Check ownership
        if agent.get('owner') != username:
            return jsonify({'error': 'Unauthorized'}), 403

        return jsonify({'agent': agent}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@workflow_bp.route('/agents/<agent_id>', methods=['PUT'])
@login_required_api
def update_agent(agent_id):
    """Update an existing agent"""
    username = session.get('username')
    data = request.get_json()

    try:
        filepath = os.path.join(AGENTS_DIR, f'{agent_id}.json')
        if not os.path.exists(filepath):
            return jsonify({'error': 'Agent not found'}), 404

        with open(filepath, 'r') as f:
            agent = json.load(f)

        # Check ownership
        if agent.get('owner') != username:
            return jsonify({'error': 'Unauthorized'}), 403

        # Update fields
        agent['name'] = data.get('name', agent['name'])
        agent['description'] = data.get('description', agent['description'])
        agent['config'] = data.get('config', agent['config'])
        agent['updated_at'] = datetime.utcnow().isoformat()

        with open(filepath, 'w') as f:
            json.dump(agent, f, indent=2)

        return jsonify({'agent': agent}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@workflow_bp.route('/agents/<agent_id>', methods=['DELETE'])
@login_required_api
def delete_agent(agent_id):
    """Delete an agent"""
    username = session.get('username')

    try:
        filepath = os.path.join(AGENTS_DIR, f'{agent_id}.json')
        if not os.path.exists(filepath):
            return jsonify({'error': 'Agent not found'}), 404

        with open(filepath, 'r') as f:
            agent = json.load(f)

        # Check ownership
        if agent.get('owner') != username:
            return jsonify({'error': 'Unauthorized'}), 403

        os.remove(filepath)
        return jsonify({'message': 'Agent deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@workflow_bp.route('/agents/<agent_id>/test', methods=['POST'])
@login_required_api
def test_agent(agent_id):
    """Test an agent with sample input"""
    username = session.get('username')
    data = request.get_json()

    try:
        filepath = os.path.join(AGENTS_DIR, f'{agent_id}.json')
        if not os.path.exists(filepath):
            return jsonify({'error': 'Agent not found'}), 404

        with open(filepath, 'r') as f:
            agent = json.load(f)

        # Check ownership
        if agent.get('owner') != username:
            return jsonify({'error': 'Unauthorized'}), 403

        # Test the agent (placeholder - implement actual testing logic)
        test_result = {
            'agent_id': agent_id,
            'test_id': str(uuid.uuid4()),
            'status': 'success',
            'input': data.get('input', {}),
            'output': {
                'message': f'Agent {agent["name"]} tested successfully (mock)',
                'agent_type': agent['type']
            },
            'execution_time_ms': 150
        }

        return jsonify({'test_result': test_result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# NODE TYPE DEFINITIONS
# ============================================================================

@workflow_bp.route('/node-types', methods=['GET'])
@login_required_api
def get_node_types():
    """Get available node types for the workflow editor"""
    return jsonify({'node_types': AGENT_NODE_TYPES}), 200


# ============================================================================
# WORKFLOW TEMPLATES
# ============================================================================

@workflow_bp.route('/templates', methods=['GET'])
@login_required_api
def get_workflow_templates():
    """Get workflow templates"""
    templates = [
        {
            'id': 'simple_tts',
            'name': 'Simple TTS Workflow',
            'description': 'Convert text to speech',
            'nodes': [
                {'id': '1', 'type': 'trigger', 'position': {'x': 100, 'y': 100}},
                {'id': '2', 'type': 'tts_agent', 'position': {'x': 300, 'y': 100}},
                {'id': '3', 'type': 'output', 'position': {'x': 500, 'y': 100}}
            ],
            'edges': [
                {'id': 'e1-2', 'source': '1', 'target': '2'},
                {'id': 'e2-3', 'source': '2', 'target': '3'}
            ]
        },
        {
            'id': 'tts_with_analysis',
            'name': 'TTS with Analysis',
            'description': 'Convert text to speech and analyze the result',
            'nodes': [
                {'id': '1', 'type': 'trigger', 'position': {'x': 100, 'y': 100}},
                {'id': '2', 'type': 'tts_agent', 'position': {'x': 300, 'y': 100}},
                {'id': '3', 'type': 'analysis_agent', 'position': {'x': 500, 'y': 100}},
                {'id': '4', 'type': 'output', 'position': {'x': 700, 'y': 100}}
            ],
            'edges': [
                {'id': 'e1-2', 'source': '1', 'target': '2'},
                {'id': 'e2-3', 'source': '2', 'target': '3'},
                {'id': 'e3-4', 'source': '3', 'target': '4'}
            ]
        }
    ]

    return jsonify({'templates': templates}), 200
