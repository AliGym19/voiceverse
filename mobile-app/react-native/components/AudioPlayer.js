/**
 * Audio Player Component
 * Plays TTS-generated audio with controls
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Animated,
  Platform,
} from 'react-native';
import { Audio } from 'expo-av';
import * as Sharing from 'expo-sharing';
import * as FileSystem from 'expo-file-system';

const THEME = {
  primary: '#1DB954',
  background: '#191414',
  surface: '#282828',
  text: '#ffffff',
  textSecondary: '#b3b3b3',
};

export default function AudioPlayer({ audioUrl, onClose, title = 'Audio' }) {
  const [sound, setSound] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [position, setPosition] = useState(0);
  const [duration, setDuration] = useState(0);
  const [slideAnim] = useState(new Animated.Value(300));

  useEffect(() => {
    loadSound();
    showPlayer();

    return () => {
      unloadSound();
    };
  }, [audioUrl]);

  /**
   * Show player with animation
   */
  const showPlayer = () => {
    Animated.spring(slideAnim, {
      toValue: 0,
      useNativeDriver: true,
      tension: 65,
      friction: 11,
    }).start();
  };

  /**
   * Hide player with animation
   */
  const hidePlayer = () => {
    Animated.timing(slideAnim, {
      toValue: 300,
      duration: 250,
      useNativeDriver: true,
    }).start(() => {
      onClose();
    });
  };

  /**
   * Load audio sound
   */
  const loadSound = async () => {
    try {
      const { sound: newSound } = await Audio.Sound.createAsync(
        { uri: audioUrl },
        { shouldPlay: false },
        onPlaybackStatusUpdate
      );

      setSound(newSound);
    } catch (error) {
      console.error('Error loading sound:', error);
      alert('Failed to load audio');
    }
  };

  /**
   * Unload sound
   */
  const unloadSound = async () => {
    if (sound) {
      await sound.unloadAsync();
      setSound(null);
    }
  };

  /**
   * Handle playback status updates
   */
  const onPlaybackStatusUpdate = (status) => {
    if (status.isLoaded) {
      setPosition(status.positionMillis);
      setDuration(status.durationMillis);
      setIsPlaying(status.isPlaying);

      if (status.didJustFinish) {
        // Replay from beginning
        sound?.setPositionAsync(0);
        setIsPlaying(false);
      }
    }
  };

  /**
   * Toggle play/pause
   */
  const togglePlayPause = async () => {
    if (!sound) return;

    if (isPlaying) {
      await sound.pauseAsync();
    } else {
      await sound.playAsync();
    }
  };

  /**
   * Seek to position
   */
  const seekTo = async (value) => {
    if (!sound) return;
    await sound.setPositionAsync(value * duration);
  };

  /**
   * Skip forward/backward
   */
  const skip = async (seconds) => {
    if (!sound) return;
    const newPosition = Math.max(0, Math.min(duration, position + seconds * 1000));
    await sound.setPositionAsync(newPosition);
  };

  /**
   * Download audio for offline use
   */
  const downloadAudio = async () => {
    try {
      const filename = `voiceverse_${Date.now()}.mp3`;
      const fileUri = `${FileSystem.documentDirectory}${filename}`;

      const downloadResumable = FileSystem.createDownloadResumable(
        audioUrl,
        fileUri
      );

      const { uri } = await downloadResumable.downloadAsync();

      alert(`Downloaded to: ${uri}`);
    } catch (error) {
      console.error('Download error:', error);
      alert('Failed to download audio');
    }
  };

  /**
   * Share audio
   */
  const shareAudio = async () => {
    try {
      if (!(await Sharing.isAvailableAsync())) {
        alert('Sharing is not available on this device');
        return;
      }

      const filename = `voiceverse_${Date.now()}.mp3`;
      const fileUri = `${FileSystem.cacheDirectory}${filename}`;

      await FileSystem.downloadAsync(audioUrl, fileUri);
      await Sharing.shareAsync(fileUri);
    } catch (error) {
      console.error('Share error:', error);
      alert('Failed to share audio');
    }
  };

  /**
   * Format time in MM:SS
   */
  const formatTime = (millis) => {
    const totalSeconds = Math.floor(millis / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <Animated.View
      style={[
        styles.container,
        { transform: [{ translateY: slideAnim }] },
      ]}
    >
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerInfo}>
          <Text style={styles.title} numberOfLines={1}>
            {title}
          </Text>
          <Text style={styles.subtitle}>VoiceVerse TTS</Text>
        </View>
        <TouchableOpacity style={styles.closeBtn} onPress={hidePlayer}>
          <Text style={styles.closeBtnText}>✕</Text>
        </TouchableOpacity>
      </View>

      {/* Progress Bar */}
      <View style={styles.progressContainer}>
        <View style={styles.progressBar}>
          <View
            style={[
              styles.progressFill,
              { width: `${(position / duration) * 100}%` },
            ]}
          />
        </View>
      </View>

      {/* Time */}
      <View style={styles.timeContainer}>
        <Text style={styles.timeText}>{formatTime(position)}</Text>
        <Text style={styles.timeText}>{formatTime(duration)}</Text>
      </View>

      {/* Controls */}
      <View style={styles.controls}>
        <TouchableOpacity
          style={styles.controlBtn}
          onPress={() => skip(-10)}
        >
          <Text style={styles.controlIcon}>⏪</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.playPauseBtn}
          onPress={togglePlayPause}
        >
          <Text style={styles.playPauseIcon}>
            {isPlaying ? '⏸' : '▶️'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.controlBtn}
          onPress={() => skip(10)}
        >
          <Text style={styles.controlIcon}>⏩</Text>
        </TouchableOpacity>
      </View>

      {/* Action Buttons */}
      <View style={styles.actions}>
        <TouchableOpacity style={styles.actionBtn} onPress={downloadAudio}>
          <Text style={styles.actionIcon}>⬇️</Text>
          <Text style={styles.actionText}>Download</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionBtn} onPress={shareAudio}>
          <Text style={styles.actionIcon}>📤</Text>
          <Text style={styles.actionText}>Share</Text>
        </TouchableOpacity>
      </View>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: THEME.surface,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    paddingBottom: Platform.OS === 'ios' ? 30 : 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  headerInfo: {
    flex: 1,
  },
  title: {
    color: THEME.text,
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 4,
  },
  subtitle: {
    color: THEME.textSecondary,
    fontSize: 14,
  },
  closeBtn: {
    width: 32,
    height: 32,
    alignItems: 'center',
    justifyContent: 'center',
  },
  closeBtnText: {
    color: THEME.text,
    fontSize: 24,
  },
  progressContainer: {
    marginBottom: 8,
  },
  progressBar: {
    height: 4,
    backgroundColor: THEME.background,
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: THEME.primary,
  },
  timeContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  timeText: {
    color: THEME.textSecondary,
    fontSize: 12,
  },
  controls: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 24,
    marginBottom: 20,
  },
  controlBtn: {
    width: 48,
    height: 48,
    alignItems: 'center',
    justifyContent: 'center',
  },
  controlIcon: {
    fontSize: 24,
  },
  playPauseBtn: {
    width: 64,
    height: 64,
    backgroundColor: THEME.primary,
    borderRadius: 32,
    alignItems: 'center',
    justifyContent: 'center',
  },
  playPauseIcon: {
    fontSize: 28,
  },
  actions: {
    flexDirection: 'row',
    gap: 12,
  },
  actionBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: THEME.background,
    padding: 12,
    borderRadius: 12,
    gap: 8,
  },
  actionIcon: {
    fontSize: 18,
  },
  actionText: {
    color: THEME.text,
    fontSize: 14,
    fontWeight: '600',
  },
});
