# -*- coding: utf-8 -*-
"""
AI Agent Executor - Wraps existing AI agents for workflow execution
Integrates all your existing agents into the visual workflow system
"""

import os
from typing import Dict, Any, List
from openai import OpenAI
from tts_agents import TTSAgentSystem
from ai_coding_agent import CodeReviewAgent, DocumentationAgent, TestGeneratorAgent


class AgentExecutor:
    """Execute AI agents as workflow nodes"""

    def __init__(self, openai_client: OpenAI = None):
        self.client = openai_client or OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        # Initialize agent systems
        self.tts_agents = TTSAgentSystem(self.client)
        self.code_review_agent = CodeReviewAgent()
        self.doc_agent = DocumentationAgent()
        self.test_agent = TestGeneratorAgent()

    def execute_node(self, node_type: str, node_config: Dict, inputs: Dict) -> Dict[str, Any]:
        """
        Execute a single agent node

        Args:
            node_type: Type of agent node (e.g., 'tts_preprocess', 'code_review')
            node_config: Node configuration (settings, parameters)
            inputs: Input data from previous nodes

        Returns:
            Dictionary with output data
        """

        # Route to appropriate agent based on node type
        if node_type == 'tts_preprocess':
            return self._execute_tts_preprocess(node_config, inputs)

        elif node_type == 'tts_chunk':
            return self._execute_tts_chunk(node_config, inputs)

        elif node_type == 'tts_metadata':
            return self._execute_tts_metadata(node_config, inputs)

        elif node_type == 'tts_voice_suggest':
            return self._execute_voice_suggest(node_config, inputs)

        elif node_type == 'tts_quality':
            return self._execute_quality_analysis(node_config, inputs)

        elif node_type == 'code_review':
            return self._execute_code_review(node_config, inputs)

        elif node_type == 'generate_docs':
            return self._execute_doc_generation(node_config, inputs)

        elif node_type == 'generate_tests':
            return self._execute_test_generation(node_config, inputs)

        elif node_type == 'custom_ai':
            return self._execute_custom_ai(node_config, inputs)

        elif node_type == 'trigger':
            # Trigger nodes just pass through inputs
            return inputs

        elif node_type == 'output':
            # Output nodes just pass through inputs
            return inputs

        else:
            raise ValueError(f"Unknown node type: {node_type}")

    # TTS Agent Executors

    def _execute_tts_preprocess(self, config: Dict, inputs: Dict) -> Dict:
        """Execute TTS preprocessing agent"""
        text = inputs.get('text', '')
        cleaned_text = self.tts_agents.preprocess_text(text)

        return {
            'text': cleaned_text,
            'original_text': text,
            'agent': 'tts_preprocess'
        }

    def _execute_tts_chunk(self, config: Dict, inputs: Dict) -> Dict:
        """Execute smart chunking agent"""
        text = inputs.get('text', '')
        max_chars = config.get('max_chars', 4000)

        chunks = self.tts_agents.smart_chunk(text, max_chars)

        return {
            'chunks': chunks,
            'chunk_count': len(chunks),
            'original_text': text,
            'agent': 'tts_chunk'
        }

    def _execute_tts_metadata(self, config: Dict, inputs: Dict) -> Dict:
        """Execute metadata suggestion agent"""
        text = inputs.get('text', '')
        metadata = self.tts_agents.suggest_metadata(text)

        return {
            'filename': metadata.get('filename', 'audio_file'),
            'category': metadata.get('category', 'Uncategorized'),
            'summary': metadata.get('summary', ''),
            'recommended_voice': metadata.get('recommended_voice', 'nova'),
            'content_type': metadata.get('content_type', 'general'),
            'text': text,
            'agent': 'tts_metadata'
        }

    def _execute_voice_suggest(self, config: Dict, inputs: Dict) -> Dict:
        """Execute voice recommendation agent"""
        text = inputs.get('text', '')
        voice, reason = self.tts_agents.suggest_voice(text)

        return {
            'recommended_voice': voice,
            'reason': reason,
            'text': text,
            'agent': 'tts_voice_suggest'
        }

    def _execute_quality_analysis(self, config: Dict, inputs: Dict) -> Dict:
        """Execute quality analysis agent"""
        text = inputs.get('text', '')
        quality = self.tts_agents.analyze_quality(text)

        return {
            'character_count': quality['character_count'],
            'word_count': quality['word_count'],
            'estimated_duration_minutes': quality['estimated_duration_minutes'],
            'issues': quality['issues'],
            'warnings': quality['warnings'],
            'quality_score': quality['quality_score'],
            'text': text,
            'agent': 'tts_quality'
        }

    # Code Agent Executors

    def _execute_code_review(self, config: Dict, inputs: Dict) -> Dict:
        """Execute code review agent"""
        code = inputs.get('code', inputs.get('text', ''))
        context = config.get('context', '')

        review = self.code_review_agent.analyze(code, context)

        return {
            'review': review,
            'code': code,
            'agent': 'code_review'
        }

    def _execute_doc_generation(self, config: Dict, inputs: Dict) -> Dict:
        """Execute documentation generation agent"""
        code = inputs.get('code', inputs.get('text', ''))
        context = config.get('context', '')

        documentation = self.doc_agent.analyze(code, context)

        return {
            'documentation': documentation,
            'code': code,
            'agent': 'generate_docs'
        }

    def _execute_test_generation(self, config: Dict, inputs: Dict) -> Dict:
        """Execute test generation agent"""
        code = inputs.get('code', inputs.get('text', ''))
        context = config.get('context', '')

        tests = self.test_agent.analyze(code, context)

        return {
            'tests': tests,
            'code': code,
            'agent': 'generate_tests'
        }

    # Custom AI Agent

    def _execute_custom_ai(self, config: Dict, inputs: Dict) -> Dict:
        """Execute custom AI agent with user-defined prompt"""
        text = inputs.get('text', inputs.get('code', ''))
        system_prompt = config.get('system_prompt', 'You are a helpful AI assistant.')
        user_prompt = config.get('user_prompt', '{text}')
        model = config.get('model', 'gpt-4o-mini')
        temperature = config.get('temperature', 0.7)

        # Replace {text} placeholder with actual input
        formatted_prompt = user_prompt.replace('{text}', text)

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=temperature,
                max_tokens=4000
            )

            result = response.choices[0].message.content

            return {
                'result': result,
                'input': text,
                'agent': 'custom_ai',
                'model': model
            }

        except Exception as e:
            return {
                'error': str(e),
                'input': text,
                'agent': 'custom_ai'
            }

    def execute_workflow(self, workflow: Dict) -> Dict[str, Any]:
        """
        Execute an entire workflow

        Args:
            workflow: Workflow definition with nodes and edges

        Returns:
            Execution results with outputs from all nodes
        """
        nodes = workflow.get('nodes', [])
        edges = workflow.get('edges', [])
        inputs = workflow.get('inputs', {})

        # Build execution graph
        node_outputs = {}

        # Find trigger node (starting point)
        trigger_nodes = [n for n in nodes if n.get('type') == 'trigger']
        if not trigger_nodes:
            return {'error': 'No trigger node found in workflow'}

        # Execute nodes in order following edges
        executed = set()
        to_execute = [trigger_nodes[0]['id']]

        while to_execute:
            current_node_id = to_execute.pop(0)

            if current_node_id in executed:
                continue

            # Find node definition
            node = next((n for n in nodes if n['id'] == current_node_id), None)
            if not node:
                continue

            # Get inputs from previous nodes
            node_inputs = {}
            incoming_edges = [e for e in edges if e.get('target') == current_node_id]

            for edge in incoming_edges:
                source_id = edge.get('source')
                if source_id in node_outputs:
                    # Merge outputs from source node
                    node_inputs.update(node_outputs[source_id])

            # Use workflow inputs for trigger node
            if node.get('type') == 'trigger':
                node_inputs = inputs

            # Execute node
            try:
                output = self.execute_node(
                    node.get('type'),
                    node.get('data', {}),
                    node_inputs
                )
                node_outputs[current_node_id] = output
            except Exception as e:
                node_outputs[current_node_id] = {'error': str(e)}

            executed.add(current_node_id)

            # Find next nodes
            outgoing_edges = [e for e in edges if e.get('source') == current_node_id]
            for edge in outgoing_edges:
                target_id = edge.get('target')
                if target_id not in executed:
                    to_execute.append(target_id)

        # Find output node results
        output_nodes = [n for n in nodes if n.get('type') == 'output']
        final_output = {}

        if output_nodes:
            for output_node in output_nodes:
                if output_node['id'] in node_outputs:
                    final_output.update(node_outputs[output_node['id']])
        else:
            # If no output node, return last executed node output
            if node_outputs:
                final_output = list(node_outputs.values())[-1]

        return {
            'status': 'completed',
            'node_outputs': node_outputs,
            'final_output': final_output,
            'nodes_executed': len(executed)
        }


# Available agent types for the visual editor
AGENT_NODE_TYPES = {
    'trigger': {
        'type': 'trigger',
        'label': 'Trigger',
        'description': 'Start the workflow',
        'category': 'flow',
        'icon': '⚡',
        'color': '#10b981',
        'inputs': [],
        'outputs': ['data']
    },
    'tts_preprocess': {
        'type': 'tts_preprocess',
        'label': 'TTS Preprocess',
        'description': 'Clean and optimize text for TTS',
        'category': 'tts',
        'icon': '🧹',
        'color': '#3b82f6',
        'inputs': ['text'],
        'outputs': ['text', 'original_text'],
        'config_fields': []
    },
    'tts_chunk': {
        'type': 'tts_chunk',
        'label': 'Smart Chunking',
        'description': 'Split text into optimal chunks',
        'category': 'tts',
        'icon': '✂️',
        'color': '#3b82f6',
        'inputs': ['text'],
        'outputs': ['chunks', 'chunk_count'],
        'config_fields': [
            {'name': 'max_chars', 'label': 'Max Characters', 'type': 'number', 'default': 4000}
        ]
    },
    'tts_metadata': {
        'type': 'tts_metadata',
        'label': 'Metadata Suggestions',
        'description': 'Generate filename, category, voice suggestions',
        'category': 'tts',
        'icon': '🏷️',
        'color': '#3b82f6',
        'inputs': ['text'],
        'outputs': ['filename', 'category', 'summary', 'recommended_voice'],
        'config_fields': []
    },
    'tts_voice_suggest': {
        'type': 'tts_voice_suggest',
        'label': 'Voice Recommendation',
        'description': 'Suggest best voice for content',
        'category': 'tts',
        'icon': '🎤',
        'color': '#3b82f6',
        'inputs': ['text'],
        'outputs': ['recommended_voice', 'reason'],
        'config_fields': []
    },
    'tts_quality': {
        'type': 'tts_quality',
        'label': 'Quality Analysis',
        'description': 'Analyze text quality and estimate duration/cost',
        'category': 'tts',
        'icon': '📊',
        'color': '#3b82f6',
        'inputs': ['text'],
        'outputs': ['quality_score', 'word_count', 'estimated_duration_minutes'],
        'config_fields': []
    },
    'code_review': {
        'type': 'code_review',
        'label': 'Code Review',
        'description': 'Review code for bugs and security issues',
        'category': 'code',
        'icon': '🔍',
        'color': '#8b5cf6',
        'inputs': ['code'],
        'outputs': ['review'],
        'config_fields': [
            {'name': 'context', 'label': 'Context', 'type': 'text', 'default': ''}
        ]
    },
    'generate_docs': {
        'type': 'generate_docs',
        'label': 'Generate Docs',
        'description': 'Generate documentation for code',
        'category': 'code',
        'icon': '📝',
        'color': '#8b5cf6',
        'inputs': ['code'],
        'outputs': ['documentation'],
        'config_fields': [
            {'name': 'context', 'label': 'Context', 'type': 'text', 'default': ''}
        ]
    },
    'generate_tests': {
        'type': 'generate_tests',
        'label': 'Generate Tests',
        'description': 'Generate test cases for code',
        'category': 'code',
        'icon': '🧪',
        'color': '#8b5cf6',
        'inputs': ['code'],
        'outputs': ['tests'],
        'config_fields': [
            {'name': 'context', 'label': 'Context', 'type': 'text', 'default': ''}
        ]
    },
    'custom_ai': {
        'type': 'custom_ai',
        'label': 'Custom AI Agent',
        'description': 'Create a custom AI agent with your own prompts',
        'category': 'ai',
        'icon': '🤖',
        'color': '#f59e0b',
        'inputs': ['text'],
        'outputs': ['result'],
        'config_fields': [
            {'name': 'system_prompt', 'label': 'System Prompt', 'type': 'textarea', 'default': 'You are a helpful AI assistant.'},
            {'name': 'user_prompt', 'label': 'User Prompt (use {text} for input)', 'type': 'textarea', 'default': '{text}'},
            {'name': 'model', 'label': 'Model', 'type': 'select', 'options': ['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo'], 'default': 'gpt-4o-mini'},
            {'name': 'temperature', 'label': 'Temperature', 'type': 'number', 'default': 0.7, 'min': 0, 'max': 2, 'step': 0.1}
        ]
    },
    'output': {
        'type': 'output',
        'label': 'Output',
        'description': 'Workflow output',
        'category': 'flow',
        'icon': '📤',
        'color': '#ef4444',
        'inputs': ['data'],
        'outputs': []
    }
}
