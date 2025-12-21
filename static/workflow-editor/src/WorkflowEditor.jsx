import React, { useCallback, useState, useEffect } from 'react';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Panel
} from 'reactflow';
import 'reactflow/dist/style.css';
import axios from 'axios';
import './WorkflowEditor.css';

// Custom node types
const nodeTypes = {
  trigger: TriggerNode,
  tts_agent: TTSAgentNode,
  analysis_agent: AnalysisAgentNode,
  tool: ToolNode,
  output: OutputNode
};

// Trigger Node Component
function TriggerNode({ data }) {
  return (
    <div className="custom-node trigger-node">
      <div className="node-header">
        <span className="node-icon">⚡</span>
        <span className="node-title">Trigger</span>
      </div>
      <div className="node-body">
        <p>Start workflow</p>
      </div>
    </div>
  );
}

// TTS Agent Node Component
function TTSAgentNode({ data }) {
  return (
    <div className="custom-node tts-agent-node">
      <div className="node-header">
        <span className="node-icon">🔊</span>
        <span className="node-title">TTS Agent</span>
      </div>
      <div className="node-body">
        <div className="node-field">
          <label>Text</label>
          <input type="text" placeholder="Enter text..." />
        </div>
        <div className="node-field">
          <label>Voice</label>
          <select>
            <option>alloy</option>
            <option>echo</option>
            <option>fable</option>
            <option>onyx</option>
            <option>nova</option>
            <option>shimmer</option>
          </select>
        </div>
        <div className="node-field">
          <label>Speed</label>
          <input type="number" min="0.25" max="4.0" step="0.25" defaultValue="1.0" />
        </div>
      </div>
    </div>
  );
}

// Analysis Agent Node Component
function AnalysisAgentNode({ data }) {
  return (
    <div className="custom-node analysis-agent-node">
      <div className="node-header">
        <span className="node-icon">🔍</span>
        <span className="node-title">Analysis Agent</span>
      </div>
      <div className="node-body">
        <div className="node-field">
          <label>Content</label>
          <textarea placeholder="Content to analyze..." />
        </div>
      </div>
    </div>
  );
}

// Tool Node Component
function ToolNode({ data }) {
  return (
    <div className="custom-node tool-node">
      <div className="node-header">
        <span className="node-icon">🔧</span>
        <span className="node-title">Tool</span>
      </div>
      <div className="node-body">
        <div className="node-field">
          <label>Tool Name</label>
          <input type="text" placeholder="Enter tool name..." />
        </div>
        <div className="node-field">
          <label>Input</label>
          <input type="text" placeholder="Tool input..." />
        </div>
      </div>
    </div>
  );
}

// Output Node Component
function OutputNode({ data }) {
  return (
    <div className="custom-node output-node">
      <div className="node-header">
        <span className="node-icon">📤</span>
        <span className="node-title">Output</span>
      </div>
      <div className="node-body">
        <p>Workflow result</p>
      </div>
    </div>
  );
}

// Initial nodes
const initialNodes = [
  {
    id: '1',
    type: 'trigger',
    position: { x: 100, y: 100 },
    data: { label: 'Start' }
  }
];

const initialEdges = [];

// Main Workflow Editor Component
export default function WorkflowEditor() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [workflows, setWorkflows] = useState([]);
  const [currentWorkflow, setCurrentWorkflow] = useState(null);
  const [workflowName, setWorkflowName] = useState('');
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [nodeTypesList, setNodeTypesList] = useState([]);

  // Load node types from API
  useEffect(() => {
    loadNodeTypes();
    loadWorkflows();
  }, []);

  const loadNodeTypes = async () => {
    try {
      const response = await axios.get('/api/workflow/node-types');
      const types = Object.values(response.data.node_types);
      setNodeTypesList(types);
    } catch (error) {
      console.error('Failed to load node types:', error);
    }
  };

  const loadWorkflows = async () => {
    try {
      const response = await axios.get('/api/workflow/workflows');
      setWorkflows(response.data.workflows);
    } catch (error) {
      console.error('Failed to load workflows:', error);
    }
  };

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const addNode = (nodeType) => {
    const newNode = {
      id: `node_${Date.now()}`,
      type: nodeType.type,
      position: { x: Math.random() * 400 + 100, y: Math.random() * 300 + 100 },
      data: {
        label: nodeType.label,
        ...nodeType
      }
    };
    setNodes((nds) => [...nds, newNode]);
  };

  const saveWorkflow = async () => {
    if (!workflowName.trim()) {
      alert('Please enter a workflow name');
      return;
    }

    try {
      const workflowData = {
        name: workflowName,
        nodes: nodes,
        edges: edges,
        description: 'Visual workflow'
      };

      if (currentWorkflow) {
        // Update existing workflow
        await axios.put(`/api/workflow/workflows/${currentWorkflow.id}`, workflowData);
        alert('Workflow updated successfully!');
      } else {
        // Create new workflow
        const response = await axios.post('/api/workflow/workflows', workflowData);
        setCurrentWorkflow(response.data.workflow);
        alert('Workflow saved successfully!');
      }

      setShowSaveDialog(false);
      loadWorkflows();
    } catch (error) {
      console.error('Failed to save workflow:', error);
      alert('Failed to save workflow: ' + error.message);
    }
  };

  const loadWorkflow = async (workflowId) => {
    try {
      const response = await axios.get(`/api/workflow/workflows/${workflowId}`);
      const workflow = response.data.workflow;

      setCurrentWorkflow(workflow);
      setWorkflowName(workflow.name);
      setNodes(workflow.nodes || []);
      setEdges(workflow.edges || []);
    } catch (error) {
      console.error('Failed to load workflow:', error);
      alert('Failed to load workflow');
    }
  };

  const executeWorkflow = async () => {
    if (!currentWorkflow) {
      alert('Please save the workflow first');
      return;
    }

    try {
      const response = await axios.post(`/api/workflow/workflows/${currentWorkflow.id}/execute`, {
        inputs: {}
      });

      alert('Workflow executed successfully!\n' + JSON.stringify(response.data.execution.outputs, null, 2));
    } catch (error) {
      console.error('Failed to execute workflow:', error);
      alert('Failed to execute workflow: ' + error.message);
    }
  };

  const clearCanvas = () => {
    if (confirm('Clear all nodes and edges?')) {
      setNodes([]);
      setEdges([]);
      setCurrentWorkflow(null);
      setWorkflowName('');
    }
  };

  return (
    <div className="workflow-editor-container">
      {/* Sidebar */}
      <div className="workflow-sidebar">
        <div className="sidebar-header">
          <h2>🌌 Workflow Editor</h2>
        </div>

        {/* Node Types */}
        <div className="sidebar-section">
          <h3>Node Types</h3>
          <div className="node-types-list">
            {nodeTypesList.map((nodeType) => (
              <button
                key={nodeType.type}
                className="node-type-button"
                onClick={() => addNode(nodeType)}
                style={{ backgroundColor: nodeType.color }}
              >
                <span className="node-type-icon">{nodeType.icon}</span>
                <span className="node-type-label">{nodeType.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Saved Workflows */}
        <div className="sidebar-section">
          <h3>Saved Workflows</h3>
          <div className="workflows-list">
            {workflows.map((workflow) => (
              <button
                key={workflow.id}
                className="workflow-item"
                onClick={() => loadWorkflow(workflow.id)}
              >
                {workflow.name}
              </button>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="sidebar-section">
          <h3>Actions</h3>
          <button className="action-button save-btn" onClick={() => setShowSaveDialog(true)}>
            💾 Save Workflow
          </button>
          <button className="action-button execute-btn" onClick={executeWorkflow}>
            ▶️ Execute
          </button>
          <button className="action-button clear-btn" onClick={clearCanvas}>
            🗑️ Clear Canvas
          </button>
        </div>
      </div>

      {/* Canvas */}
      <div className="workflow-canvas">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
        >
          <Controls />
          <MiniMap />
          <Background variant="dots" gap={12} size={1} />

          <Panel position="top-left">
            <div className="workflow-title">
              {currentWorkflow ? currentWorkflow.name : 'New Workflow'}
            </div>
          </Panel>
        </ReactFlow>
      </div>

      {/* Save Dialog */}
      {showSaveDialog && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h2>Save Workflow</h2>
            <input
              type="text"
              placeholder="Workflow name..."
              value={workflowName}
              onChange={(e) => setWorkflowName(e.target.value)}
              className="workflow-name-input"
            />
            <div className="modal-actions">
              <button onClick={saveWorkflow} className="btn-primary">Save</button>
              <button onClick={() => setShowSaveDialog(false)} className="btn-secondary">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
