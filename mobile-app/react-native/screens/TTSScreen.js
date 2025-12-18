/**
 * TTS Generation Screen
 * Main interface for text-to-speech generation
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  Alert,
  Platform,
} from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import { ttsAPI, aiAPI, fileAPI } from '../services/api';
import AudioPlayer from '../components/AudioPlayer';

const VOICES = [
  { id: 'alloy', name: 'Alloy', emoji: '🎤' },
  { id: 'echo', name: 'Echo', emoji: '🔊' },
  { id: 'fable', name: 'Fable', emoji: '📖' },
  { id: 'onyx', name: 'Onyx', emoji: '🎧' },
  { id: 'nova', name: 'Nova', emoji: '✨' },
  { id: 'shimmer', name: 'Shimmer', emoji: '🌟' },
];

const THEME = {
  primary: '#1DB954',
  background: '#191414',
  surface: '#282828',
  text: '#ffffff',
  textSecondary: '#b3b3b3',
};

export default function TTSScreen() {
  const [text, setText] = useState('');
  const [selectedVoice, setSelectedVoice] = useState('alloy');
  const [speed, setSpeed] = useState(1.0);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isPreprocessing, setIsPreprocessing] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const [showPlayer, setShowPlayer] = useState(false);

  /**
   * Handle TTS generation
   */
  const handleGenerate = async () => {
    if (!text.trim()) {
      Alert.alert('Error', 'Please enter some text');
      return;
    }

    try {
      setIsGenerating(true);

      const result = await ttsAPI.generate(text, selectedVoice, speed);

      if (result.audio_url || result.url) {
        setAudioUrl(result.audio_url || result.url);
        setShowPlayer(true);
        Alert.alert('Success', 'Speech generated successfully!');
      } else {
        throw new Error('No audio URL in response');
      }
    } catch (error) {
      Alert.alert('Error', error.message || 'Failed to generate speech');
    } finally {
      setIsGenerating(false);
    }
  };

  /**
   * Handle AI text preprocessing
   */
  const handlePreprocess = async () => {
    if (!text.trim()) {
      Alert.alert('Error', 'Please enter some text');
      return;
    }

    try {
      setIsPreprocessing(true);

      const processedText = await aiAPI.preprocess(text);
      setText(processedText);

      Alert.alert('Success', 'Text preprocessed with AI!');
    } catch (error) {
      Alert.alert('Error', error.message || 'Failed to preprocess text');
    } finally {
      setIsPreprocessing(false);
    }
  };

  /**
   * Handle file upload (PDF/DOCX)
   */
  const handleFileUpload = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
        copyToCacheDirectory: true,
      });

      if (result.type === 'success') {
        // Extract text from file
        const extractedText = await fileAPI.uploadFile(result.uri, result.name);
        setText(extractedText);

        Alert.alert('Success', 'Text extracted from file');
      }
    } catch (error) {
      Alert.alert('Error', error.message || 'Failed to upload file');
    }
  };

  /**
   * Get recommended voice based on text
   */
  const handleVoiceRecommendation = async () => {
    if (!text.trim()) {
      Alert.alert('Error', 'Please enter some text first');
      return;
    }

    try {
      const recommendedVoice = await aiAPI.recommendVoice(text);
      setSelectedVoice(recommendedVoice);

      Alert.alert(
        'Voice Recommended',
        `AI suggests using the "${recommendedVoice}" voice for this text`
      );
    } catch (error) {
      console.error('Voice recommendation error:', error);
    }
  };

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollView}>
        {/* Text Input */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Text to Convert</Text>
          <TextInput
            style={styles.textInput}
            value={text}
            onChangeText={setText}
            placeholder="Enter or paste text here..."
            placeholderTextColor={THEME.textSecondary}
            multiline
            textAlignVertical="top"
          />

          {/* Quick Actions */}
          <View style={styles.quickActions}>
            <TouchableOpacity
              style={styles.quickActionBtn}
              onPress={handleFileUpload}
            >
              <Text style={styles.quickActionText}>📄 Upload File</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.quickActionBtn}
              onPress={handlePreprocess}
              disabled={isPreprocessing}
            >
              {isPreprocessing ? (
                <ActivityIndicator size="small" color={THEME.primary} />
              ) : (
                <Text style={styles.quickActionText}>✨ AI Preprocess</Text>
              )}
            </TouchableOpacity>
          </View>
        </View>

        {/* Voice Selection */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Voice</Text>
            <TouchableOpacity
              onPress={handleVoiceRecommendation}
              style={styles.recommendBtn}
            >
              <Text style={styles.recommendText}>Get Recommendation</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.voiceGrid}>
            {VOICES.map((voice) => (
              <TouchableOpacity
                key={voice.id}
                style={[
                  styles.voiceBtn,
                  selectedVoice === voice.id && styles.voiceBtnActive,
                ]}
                onPress={() => setSelectedVoice(voice.id)}
              >
                <Text style={styles.voiceEmoji}>{voice.emoji}</Text>
                <Text
                  style={[
                    styles.voiceText,
                    selectedVoice === voice.id && styles.voiceTextActive,
                  ]}
                >
                  {voice.name}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Speed Control */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Speed: {speed.toFixed(1)}x</Text>
          <View style={styles.speedControl}>
            <TouchableOpacity
              style={styles.speedBtn}
              onPress={() => setSpeed(Math.max(0.5, speed - 0.1))}
            >
              <Text style={styles.speedBtnText}>−</Text>
            </TouchableOpacity>

            <View style={styles.speedDisplay}>
              <Text style={styles.speedText}>{speed.toFixed(1)}x</Text>
            </View>

            <TouchableOpacity
              style={styles.speedBtn}
              onPress={() => setSpeed(Math.min(2.0, speed + 0.1))}
            >
              <Text style={styles.speedBtnText}>+</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.speedPresets}>
            {[0.5, 0.75, 1.0, 1.25, 1.5, 2.0].map((preset) => (
              <TouchableOpacity
                key={preset}
                style={[
                  styles.presetBtn,
                  speed === preset && styles.presetBtnActive,
                ]}
                onPress={() => setSpeed(preset)}
              >
                <Text
                  style={[
                    styles.presetText,
                    speed === preset && styles.presetTextActive,
                  ]}
                >
                  {preset}x
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Generate Button */}
        <TouchableOpacity
          style={[
            styles.generateBtn,
            isGenerating && styles.generateBtnDisabled,
          ]}
          onPress={handleGenerate}
          disabled={isGenerating}
        >
          {isGenerating ? (
            <>
              <ActivityIndicator size="small" color={THEME.background} />
              <Text style={styles.generateText}>Generating...</Text>
            </>
          ) : (
            <Text style={styles.generateText}>🎙️ Generate Speech</Text>
          )}
        </TouchableOpacity>

        {/* Character count */}
        <Text style={styles.charCount}>
          {text.length} characters • Est. cost: $
          {((text.length / 1000) * 0.015).toFixed(4)}
        </Text>
      </ScrollView>

      {/* Audio Player */}
      {showPlayer && audioUrl && (
        <AudioPlayer
          audioUrl={audioUrl}
          onClose={() => setShowPlayer(false)}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: THEME.background,
  },
  scrollView: {
    flex: 1,
    padding: 16,
  },
  section: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: THEME.text,
    marginBottom: 12,
  },
  recommendBtn: {
    padding: 8,
  },
  recommendText: {
    color: THEME.primary,
    fontSize: 14,
    fontWeight: '600',
  },
  textInput: {
    backgroundColor: THEME.surface,
    borderRadius: 12,
    padding: 16,
    color: THEME.text,
    fontSize: 16,
    minHeight: 150,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  quickActions: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 12,
  },
  quickActionBtn: {
    flex: 1,
    backgroundColor: THEME.surface,
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  quickActionText: {
    color: THEME.text,
    fontSize: 14,
    fontWeight: '600',
  },
  voiceGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  voiceBtn: {
    flex: 1,
    minWidth: '30%',
    backgroundColor: THEME.surface,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'transparent',
  },
  voiceBtnActive: {
    backgroundColor: THEME.primary,
    borderColor: THEME.primary,
  },
  voiceEmoji: {
    fontSize: 24,
    marginBottom: 4,
  },
  voiceText: {
    color: THEME.text,
    fontSize: 14,
    fontWeight: '600',
  },
  voiceTextActive: {
    color: THEME.background,
  },
  speedControl: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
    marginBottom: 12,
  },
  speedBtn: {
    width: 44,
    height: 44,
    backgroundColor: THEME.surface,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
  },
  speedBtnText: {
    color: THEME.text,
    fontSize: 24,
    fontWeight: '700',
  },
  speedDisplay: {
    flex: 1,
    backgroundColor: THEME.surface,
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  speedText: {
    color: THEME.text,
    fontSize: 20,
    fontWeight: '700',
  },
  speedPresets: {
    flexDirection: 'row',
    gap: 8,
  },
  presetBtn: {
    flex: 1,
    backgroundColor: THEME.surface,
    padding: 8,
    borderRadius: 8,
    alignItems: 'center',
  },
  presetBtnActive: {
    backgroundColor: THEME.primary,
  },
  presetText: {
    color: THEME.textSecondary,
    fontSize: 12,
    fontWeight: '600',
  },
  presetTextActive: {
    color: THEME.background,
  },
  generateBtn: {
    backgroundColor: THEME.primary,
    padding: 18,
    borderRadius: 24,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 8,
  },
  generateBtnDisabled: {
    opacity: 0.6,
  },
  generateText: {
    color: THEME.background,
    fontSize: 18,
    fontWeight: '700',
  },
  charCount: {
    color: THEME.textSecondary,
    fontSize: 12,
    textAlign: 'center',
    marginTop: 8,
  },
});
