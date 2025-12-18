# AI Agents for TTS App - Complete Guide

## Overview

Your TTS application now includes powerful AI agents that enhance text-to-speech generation quality and user experience. These agents use OpenAI's GPT-4o-mini model to intelligently process, analyze, and optimize text before converting it to speech.

## Features Added

### 1. **Smart Text Preprocessing Agent** ✨
**What it does:**
- Cleans and optimizes text for natural TTS output
- Fixes formatting artifacts from PDF/DOCX parsing
- Expands URLs to readable format (e.g., "example dot com")
- Expands acronyms (e.g., "NASA" → "N A S A")
- Converts numbers to words when appropriate
- Removes non-spoken elements (page numbers, headers)

**When to use:**
- Parsed content from PDFs or Word documents
- Text with URLs or technical jargon
- Content with formatting issues

### 2. **Smart Chunking Agent** ✂️
**What it does:**
- Intelligently splits text longer than 4,096 characters
- Splits at natural boundaries (paragraphs, sentences)
- Maintains context and flow between chunks
- Prevents awkward mid-sentence cuts

**When to use:**
- Long articles, blog posts, or documents
- Any text over 4,096 characters
- Content that needs to maintain narrative flow

**Previous behavior:** Text was simply truncated at 4,096 characters
**New behavior:** AI finds optimal split points and creates meaningful chunks

### 3. **Metadata Suggestion Agent** 💡
**What it does:**
- Analyzes content and suggests optimal filename
- Recommends appropriate category/group
- Generates summary of content
- Suggests best voice for the content type
- Identifies content type (narration, dialogue, technical)

**When to use:**
- When you're not sure what to name the file
- For organizing large batches of content
- To quickly categorize new content

### 4. **Quality Analysis Agent** 📊
**What it does:**
- Analyzes text for TTS suitability
- Detects problematic patterns (code, URLs, long numbers)
- Estimates listening duration
- Provides quality score and recommendations
- Warns about potential issues

**When to use:**
- Before generating expensive long-form content
- To validate text quality
- To estimate costs and duration

### 5. **Voice Recommendation Agent** 🎤
**What it does:**
- Analyzes content tone and style
- Recommends optimal voice from 6 options
- Provides reasoning for recommendation

**Available Voices:**
- `alloy`: Neutral, versatile (tutorials, documentation)
- `echo`: Male, clear (technical content, professional)
- `fable`: British male (storytelling, audiobooks)
- `onyx`: Deep male (authority, news, formal)
- `nova`: Female, warm (friendly content, guides)
- `shimmer`: Soft female (meditation, calm narration)

## User Interface

### New UI Elements

1. **AI Agent Features Section** (purple/violet styled box)
   - Located above the "Generate Audio" button
   - Contains toggles and action buttons

2. **Toggles:**
   - ✨ Smart Text Preprocessing (checkbox)
   - ✂️ Smart Chunking (checkbox)

3. **Action Buttons:**
   - 💡 Get AI Suggestions (auto-fills form fields)
   - 📊 Analyze Text Quality (shows analysis results)

### How to Use in the Web UI

1. **Enable Smart Features:**
   ```
   1. Enter or paste your text
   2. Check "Smart Text Preprocessing" for better quality
   3. Check "Smart Chunking" if text is over 4,096 chars
   4. Click "Generate Audio"
   ```

2. **Get AI Suggestions:**
   ```
   1. Enter your text
   2. Click "💡 Get AI Suggestions"
   3. Wait for AI to analyze (2-5 seconds)
   4. Form fields auto-fill with suggestions
   5. Review and adjust if needed
   6. Click "Generate Audio"
   ```

3. **Analyze Text Quality:**
   ```
   1. Enter your text
   2. Click "📊 Analyze Text Quality"
   3. Review analysis results:
      - Character/word count
      - Estimated duration
      - Quality score
      - Warnings and issues
   4. Fix any issues if needed
   5. Click "Generate Audio"
   ```

## API Endpoints

All endpoints require authentication (`@login_required`).

### 1. Preprocess Text
```
POST /api/agent/preprocess
Content-Type: application/json

{
    "text": "Your text here..."
}

Response:
{
    "success": true,
    "original_text": "...",
    "processed_text": "...",
    "original_length": 1234,
    "processed_length": 1200
}
```

### 2. Get Metadata Suggestions
```
POST /api/agent/suggest-metadata
Content-Type: application/json

{
    "text": "Your text here..."
}

Response:
{
    "success": true,
    "suggestions": {
        "filename": "ai_podcast_intro",
        "category": "Education",
        "summary": "Introduction to AI and ML",
        "recommended_voice": "nova",
        "content_type": "narration"
    }
}
```

### 3. Analyze Text Quality
```
POST /api/agent/analyze
Content-Type: application/json

{
    "text": "Your text here..."
}

Response:
{
    "success": true,
    "analysis": {
        "character_count": 1234,
        "word_count": 200,
        "estimated_duration_minutes": 1.3,
        "issues": ["Contains code-like syntax..."],
        "warnings": ["Text is 5000 characters..."],
        "quality_score": 85
    }
}
```

### 4. Smart Chunk Text
```
POST /api/agent/smart-chunk
Content-Type: application/json

{
    "text": "Your long text here...",
    "max_chars": 4000
}

Response:
{
    "success": true,
    "chunks": [
        {
            "text": "Chunk 1 text...",
            "chunk_number": 1,
            "total_chunks": 3,
            "chars": 3800
        },
        ...
    ],
    "total_chunks": 3
}
```

## Technical Details

### Files Added/Modified

1. **`tts_agents.py`** (NEW)
   - Main AI agents module
   - Contains `TTSAgentSystem` class
   - All agent logic and AI interactions

2. **`tts_app19.py`** (MODIFIED)
   - Added agent import and initialization
   - Added 4 new API endpoints
   - Integrated agents into TTS generation flow
   - Added UI elements and JavaScript functions
   - Added CSS styles for agent features

3. **`test_agents.py`** (NEW)
   - Test suite for all agent functions
   - Validates each agent independently

### Dependencies

- `openai>=1.0.0` (already installed)
- No new dependencies required!

### Cost Considerations

Each AI agent call uses GPT-4o-mini which is very affordable:
- **Input:** $0.150 per 1M tokens (~$0.00015 per 1K tokens)
- **Output:** $0.600 per 1M tokens (~$0.0006 per 1K tokens)

**Typical costs per operation:**
- Preprocessing: ~$0.001-0.002 per request
- Metadata suggestions: ~$0.0005-0.001 per request
- Quality analysis: ~$0.0002-0.0005 per request
- Smart chunking: ~$0.001-0.003 per request

Much cheaper than the TTS generation itself ($0.015 per 1K chars).

## Testing

Run the test suite to verify everything works:

```bash
cd /Users/ali/Desktop/Project
python3 test_agents.py
```

Expected output:
```
===========================================================
TTS AI AGENTS TEST SUITE
===========================================================

Testing: Text Preprocessing Agent
...
✅ Preprocessing test completed

Testing: Smart Chunking Agent
...
✅ Chunking test completed

...

✅ ALL TESTS COMPLETED SUCCESSFULLY!
```

## Usage Examples

### Example 1: Processing a Long Article

```python
from tts_agents import create_agent_system

# Create agent system
agents = create_agent_system()

# Your long article
article = """[5000+ characters of text]"""

# Step 1: Preprocess
cleaned = agents.preprocess_text(article)

# Step 2: Chunk if needed
chunks = agents.smart_chunk(cleaned, max_chars=4000)

# Step 3: Generate TTS for each chunk
for chunk in chunks:
    # Generate audio for chunk['text']
    print(f"Processing chunk {chunk['chunk_number']}/{chunk['total_chunks']}")
```

### Example 2: Auto-Organizing Content

```python
from tts_agents import create_agent_system

agents = create_agent_system()
text = "Your content here..."

# Get AI suggestions
suggestions = agents.suggest_metadata(text)

print(f"Filename: {suggestions['filename']}")
print(f"Category: {suggestions['category']}")
print(f"Voice: {suggestions['recommended_voice']}")
```

### Example 3: Quality Checking Before Generation

```python
from tts_agents import create_agent_system

agents = create_agent_system()
text = "Your content with URLs and code..."

# Analyze quality
analysis = agents.analyze_quality(text)

if analysis['quality_score'] < 70:
    print("Warning: Text may not be suitable for TTS")
    print(f"Issues: {analysis['issues']}")
else:
    print(f"Quality score: {analysis['quality_score']}/100 - Good to go!")
```

## Best Practices

1. **Use preprocessing for parsed content:**
   - Always enable for PDF/DOCX uploads
   - Significantly improves audio quality

2. **Enable smart chunking for long content:**
   - Better than simple truncation
   - Maintains narrative flow

3. **Check quality before batch processing:**
   - Saves costs on unsuitable content
   - Identifies issues early

4. **Use AI suggestions for consistency:**
   - Helps organize large content libraries
   - Ensures consistent naming

5. **Combine multiple agents:**
   ```
   1. Analyze quality
   2. Get metadata suggestions
   3. Enable preprocessing
   4. Enable smart chunking
   5. Generate audio
   ```

## Troubleshooting

### Agent calls failing?
- Check OPENAI_API_KEY is set correctly
- Verify API key has sufficient credits
- Check network connectivity

### Slow responses?
- Normal: AI calls take 2-5 seconds
- Use agents selectively for better UX
- Consider caching for repeated content

### Preprocessing not improving quality?
- AI works best on messy/formatted text
- Clean text may not show much improvement
- Local preprocessing still provides value

## Future Enhancements

Potential additions you could make:

1. **Multi-chunk audio merging**
   - Automatically generate and merge multiple audio files
   - Create chapters/bookmarks

2. **Batch processing**
   - Process multiple texts with agents
   - Bulk generate with smart settings

3. **Voice fine-tuning**
   - Analyze voice preferences over time
   - Learn user preferences

4. **Content caching**
   - Cache AI suggestions for similar content
   - Reduce API calls and costs

5. **Advanced preprocessing**
   - Detect and preserve markdown formatting
   - Handle tables and lists better
   - Custom pronunciation dictionaries

## Support

For issues or questions:
1. Check the test suite: `python3 test_agents.py`
2. Review server logs for errors
3. Verify API key and credits
4. Check browser console for JS errors

## Summary

You now have a production-ready AI agent system integrated into your TTS app! The agents:

✅ Improve audio quality (preprocessing)
✅ Handle long texts intelligently (chunking)
✅ Automate organization (metadata suggestions)
✅ Prevent costly mistakes (quality analysis)
✅ Optimize voice selection (recommendations)

**Start using them now by running your app:**
```bash
cd /Users/ali/Desktop/Project
python3 tts_app19.py
```

Then navigate to the app and look for the purple "🤖 AI Agent Features" section!
