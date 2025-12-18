# -*- coding: utf-8 -*-
"""
TTS AI Agents Module
Intelligent agents for text preprocessing, chunking, and content analysis
"""

import re
from openai import OpenAI
import os
from typing import List, Dict, Tuple


class TTSAgentSystem:
    """Main AI Agent System for TTS optimization"""

    def __init__(self, openai_client: OpenAI = None):
        self.client = openai_client or OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def preprocess_text(self, text: str) -> str:
        """
        Intelligent text preprocessing for optimal TTS output
        - Fixes formatting issues
        - Handles URLs, acronyms, numbers
        - Removes artifacts from PDF/DOCX parsing
        """
        try:
            # Quick local preprocessing first
            text = self._local_preprocess(text)

            # Use AI for intelligent cleanup
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a text preprocessing expert for text-to-speech conversion.
Clean and optimize the text for natural speech synthesis:
- Fix formatting artifacts (extra spaces, line breaks)
- Expand URLs to readable format (e.g., "example dot com")
- Expand acronyms that should be spoken letter-by-letter (e.g., "N A S A")
- Convert numbers to words when appropriate (e.g., "2024" to "twenty twenty-four")
- Remove non-spoken elements (page numbers, headers, footers)
- Keep the meaning and content intact
- Return ONLY the cleaned text, no explanations."""
                    },
                    {
                        "role": "user",
                        "content": f"Clean this text for TTS:\n\n{text[:3000]}"  # Limit for API
                    }
                ],
                temperature=0.3,
                max_tokens=4000
            )

            cleaned_text = response.choices[0].message.content.strip()
            return cleaned_text

        except Exception as e:
            print(f"⚠️ Preprocessing agent error: {e}")
            return self._local_preprocess(text)

    def _local_preprocess(self, text: str) -> str:
        """Local preprocessing without AI (fallback)"""
        # Fix multiple spaces
        text = re.sub(r'\s+', ' ', text)

        # Fix common PDF artifacts
        text = re.sub(r'-\s+\n\s+', '', text)  # Remove hyphenation
        text = re.sub(r'\n+', '\n', text)  # Fix multiple newlines

        # Add periods to common abbreviations for natural pauses
        text = re.sub(r'\bMr\b', 'Mr.', text)
        text = re.sub(r'\bDr\b', 'Dr.', text)
        text = re.sub(r'\bMs\b', 'Ms.', text)

        return text.strip()

    def smart_chunk(self, text: str, max_chars: int = 4000) -> List[Dict[str, any]]:
        """
        Intelligently split text into chunks at natural boundaries
        Returns list of chunks with metadata
        """
        if len(text) <= max_chars:
            return [{
                'text': text,
                'chunk_number': 1,
                'total_chunks': 1,
                'chars': len(text)
            }]

        try:
            # Use AI to find optimal split points
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are a text chunking expert. Split the text into chunks of approximately {max_chars} characters each.
Rules:
- Split at natural boundaries (paragraph breaks, section endings, sentence endings)
- Each chunk should be self-contained and make sense
- Maintain context and flow between chunks
- Return a JSON array with: [{{"chunk_text": "...", "chunk_title": "brief description"}}]
- Aim for {max_chars} characters per chunk but prioritize natural breaks"""
                    },
                    {
                        "role": "user",
                        "content": f"Split this text into optimal chunks:\n\n{text[:8000]}"
                    }
                ],
                temperature=0.3,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )

            import json
            result = json.loads(response.choices[0].message.content)

            if 'chunks' in result and isinstance(result['chunks'], list):
                chunks = []
                for i, chunk_data in enumerate(result['chunks'], 1):
                    chunks.append({
                        'text': chunk_data.get('chunk_text', ''),
                        'title': chunk_data.get('chunk_title', f'Part {i}'),
                        'chunk_number': i,
                        'total_chunks': len(result['chunks']),
                        'chars': len(chunk_data.get('chunk_text', ''))
                    })
                return chunks

        except Exception as e:
            print(f"⚠️ Smart chunking agent error: {e}, falling back to simple chunking")

        # Fallback to simple sentence-based chunking
        return self._simple_chunk(text, max_chars)

    def _simple_chunk(self, text: str, max_chars: int) -> List[Dict[str, any]]:
        """Simple sentence-based chunking (fallback)"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 <= max_chars:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "

        if current_chunk:
            chunks.append(current_chunk.strip())

        return [
            {
                'text': chunk,
                'chunk_number': i + 1,
                'total_chunks': len(chunks),
                'chars': len(chunk)
            }
            for i, chunk in enumerate(chunks)
        ]

    def suggest_metadata(self, text: str) -> Dict[str, str]:
        """
        Generate smart metadata suggestions
        - Filename
        - Category/Group
        - Summary
        - Recommended voice
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """Analyze text and suggest metadata for TTS audio file.
Available voices: alloy (neutral), echo (male), fable (British male), onyx (deep male), nova (female), shimmer (soft female)

Return JSON with:
- filename: short descriptive name (no spaces, use underscores, max 30 chars)
- category: single word category (Education, Entertainment, Business, Story, News, etc.)
- summary: one sentence summary (max 100 chars)
- recommended_voice: best voice for this content
- content_type: type (narration, dialogue, technical, casual)"""
                    },
                    {
                        "role": "user",
                        "content": f"Analyze this text:\n\n{text[:2000]}"
                    }
                ],
                temperature=0.5,
                max_tokens=300,
                response_format={"type": "json_object"}
            )

            import json
            suggestions = json.loads(response.choices[0].message.content)
            return suggestions

        except Exception as e:
            print(f"⚠️ Metadata suggestion agent error: {e}")
            return {
                'filename': 'audio_file',
                'category': 'Uncategorized',
                'summary': 'TTS audio file',
                'recommended_voice': 'nova',
                'content_type': 'general'
            }

    def analyze_quality(self, text: str) -> Dict[str, any]:
        """
        Analyze text quality and provide recommendations
        """
        issues = []
        warnings = []

        # Check length
        if len(text) > 4096:
            warnings.append(f"Text is {len(text)} characters (limit: 4096). Will be chunked.")

        # Check for problematic patterns
        if re.search(r'```|<code>|{|}|\[|\]', text):
            issues.append("Contains code-like syntax that may not sound natural")

        if len(re.findall(r'http[s]?://', text)) > 5:
            issues.append("Contains many URLs that may not sound natural")

        if len(re.findall(r'\d{4,}', text)) > 10:
            issues.append("Contains many long numbers that may be hard to listen to")

        # Estimate listening time (avg speaking rate: 150 words per minute)
        word_count = len(text.split())
        estimated_minutes = word_count / 150

        return {
            'character_count': len(text),
            'word_count': word_count,
            'estimated_duration_minutes': round(estimated_minutes, 1),
            'issues': issues,
            'warnings': warnings,
            'quality_score': max(0, 100 - (len(issues) * 20) - (len(warnings) * 10))
        }

    def suggest_voice(self, text: str) -> Tuple[str, str]:
        """
        Suggest the best voice based on content analysis
        Returns: (voice_name, reason)
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """Recommend the best TTS voice based on content.
Available voices:
- alloy: neutral, versatile
- echo: male, clear
- fable: British male, storytelling
- onyx: deep male, authoritative
- nova: female, warm
- shimmer: soft female, gentle

Return JSON: {"voice": "voice_name", "reason": "brief explanation"}"""
                    },
                    {
                        "role": "user",
                        "content": f"Recommend voice for:\n\n{text[:1000]}"
                    }
                ],
                temperature=0.3,
                max_tokens=100,
                response_format={"type": "json_object"}
            )

            import json
            result = json.loads(response.choices[0].message.content)
            return result.get('voice', 'nova'), result.get('reason', 'General purpose')

        except Exception as e:
            print(f"⚠️ Voice suggestion agent error: {e}")
            return 'nova', 'Default voice'


# Convenience functions for easy integration
def create_agent_system(openai_client=None) -> TTSAgentSystem:
    """Create and return a new agent system instance"""
    return TTSAgentSystem(openai_client)
