# 🤖 AI Agent Visual Editor - Quick Start Guide

## ✨ What You Now Have

A fully integrated visual AI agent platform directly in your VoiceVerse app! Build drag-and-drop workflows with your existing AI agents.

## 🚀 How to Start

### 1. **Start Your App**

```bash
cd /Users/ali/Desktop/Project
python3 tts_app19.py
```

### 2. **Login as Admin**

- **URL**: http://localhost:5000
- **Username**: `admin`
- **Password**: `Admin@123456789`

⚠️ **IMPORTANT**: Change this password immediately after first login!

### 3. **Access AI Agents**

Once logged in as admin, you'll see a new menu item:
- **🤖 AI Agents** - Click this to open the visual editor

## 🎯 Available Agent Nodes

### **Flow Control**
- **⚡ Trigger** - Start point for workflows
- **📤 Output** - End point for workflows

### **TTS Agents**
- **🧹 TTS Preprocess** - Clean text for TTS
- **✂️ Smart Chunking** - Split long text intelligently
- **🏷️ Metadata Suggestions** - Generate filenames, categories
- **🎤 Voice Recommendation** - Suggest best voice
- **📊 Quality Analysis** - Analyze text quality

### **Code Agents**
- **🔍 Code Review** - Review code for bugs/security
- **📝 Generate Docs** - Create documentation
- **🧪 Generate Tests** - Create test cases

### **Custom**
- **🤖 Custom AI Agent** - Create your own agent with custom prompts

## 📝 How to Use

### **Create Your First Workflow**

1. **Drag Nodes** from the left sidebar onto the canvas
2. **Connect Nodes** by dragging from the green dots
3. **Configure Nodes** by clicking on them (if they have config options)
4. **Save Workflow** - Click "Save Workflow" button
5. **Test Workflow** - Click "Test Workflow", enter input text, and execute

### **Example Workflow: Smart TTS Pipeline**

```
Trigger → TTS Preprocess → Voice Recommendation → Output
```

This workflow:
1. Takes input text
2. Cleans it for TTS
3. Suggests the best voice
4. Returns cleaned text + voice recommendation

### **Example Workflow: Code Documentation Generator**

```
Trigger → Code Review → Generate Docs → Generate Tests → Output
```

This workflow:
1. Takes code as input
2. Reviews it for issues
3. Generates documentation
4. Creates test cases
5. Returns everything

## 🔧 Custom AI Agents

Create your own AI agents with custom prompts:

1. Drag "Custom AI Agent" node to canvas
2. Click to configure:
   - **System Prompt**: Define the agent's role
   - **User Prompt**: Template for input (use `{text}` placeholder)
   - **Model**: Choose GPT model
   - **Temperature**: Control creativity (0-2)

**Example Custom Agent - Summarizer**:
- System Prompt: `You are an expert summarizer`
- User Prompt: `Summarize this text in 3 sentences: {text}`
- Model: `gpt-4o-mini`
- Temperature: `0.3`

## 💾 Managing Workflows

### **Save Workflow**
- Click "Save Workflow"
- Enter name and description
- Workflows are saved per user

### **Load Workflow**
- Click "Load"
- Select from your saved workflows
- Edit and re-save

### **Execute Workflow**
1. Save your workflow first
2. Click "Test Workflow"
3. Enter input text
4. Click "Execute"
5. View results in JSON format

## 🔐 Admin Features

Only admin users can:
- Access `/ai-agents` visual editor
- Create and manage workflows
- See the "AI Agents" menu item

**To make another user admin**:
```bash
cd /Users/ali/Desktop/Project
sqlite3 voiceverse.db "UPDATE users SET is_admin = 1 WHERE username = 'username_here';"
```

## 📊 Workflow Execution

When you execute a workflow:
1. Input goes to the Trigger node
2. Data flows through connected nodes
3. Each node processes and passes data forward
4. Output node returns final result

**Data Passed Between Nodes**:
- Trigger: `{text: "your input"}`
- TTS Preprocess: `{text: "cleaned", original_text: "..."}`
- Voice Suggest: `{recommended_voice: "nova", reason: "..."}`
- Metadata: `{filename: "...", category: "...", recommended_voice: "..."}`

## 🛠️ API Endpoints

The visual editor uses these API endpoints:

- `GET /api/workflow/node-types` - Get available nodes
- `GET /api/workflow/workflows` - List your workflows
- `POST /api/workflow/workflows` - Save workflow
- `PUT /api/workflow/workflows/<id>` - Update workflow
- `DELETE /api/workflow/workflows/<id>` - Delete workflow
- `POST /api/workflow/workflows/<id>/execute` - Execute workflow

## 🎨 Tips & Tricks

1. **Start Simple**: Begin with 2-3 nodes, test, then expand
2. **Use Trigger & Output**: Every workflow needs these
3. **Test Often**: Use "Test Workflow" to verify each step
4. **Chain Agents**: Connect TTS agents for complex pipelines
5. **Custom Agents**: Create specialized agents for your needs

## 🐛 Troubleshooting

### **Can't see AI Agents menu**
- Ensure you're logged in as admin
- Check: `sqlite3 voiceverse.db "SELECT username, is_admin FROM users;"`

### **Workflow won't execute**
- Make sure workflow is saved first
- Check that all nodes are connected
- Verify input format (should have `text` field)

### **Agent execution fails**
- Check `OPENAI_API_KEY` is set in `.env`
- Verify API key has credits
- Check console for error messages

### **Visual editor not loading**
- Check that `static/agent_editor.html` exists
- Try refreshing the page (Ctrl+F5)
- Check browser console for errors

## 📚 Next Steps

1. **Create your first workflow**
2. **Test with different inputs**
3. **Combine multiple agents**
4. **Build custom agents for your needs**
5. **Share workflows with your team** (export/import coming soon)

## 🎯 Example Use Cases

### **Content Writer Assistant**
```
Trigger → TTS Preprocess → Quality Analysis → Voice Recommendation → Metadata Suggestions → Output
```
Takes raw text, cleans it, analyzes quality, suggests voice and filename.

### **Code Quality Pipeline**
```
Trigger → Code Review → Generate Tests → Generate Docs → Output
```
Complete code review, testing, and documentation generation.

### **Smart Summarizer**
```
Trigger → Custom AI (Summarize) → Custom AI (Extract Keywords) → Output
```
Summarizes text and extracts key points.

---

## 🆘 Support

- Check the main README.md for VoiceVerse documentation
- API documentation: http://localhost:5000/api-docs
- Security guide: SECURITY.md

**Enjoy building with your AI agents!** 🚀
