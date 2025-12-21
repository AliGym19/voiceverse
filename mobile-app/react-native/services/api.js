/**
 * VoiceVerse API Service
 * Handles all communication with Flask backend
 */

import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as FileSystem from 'expo-file-system';

// API Configuration
const API_CONFIG = {
  // CHANGE THIS TO YOUR FLASK SERVER URL
  baseURL: __DEV__
    ? 'http://localhost:5000'  // Development (use your computer's IP for real device testing)
    : 'https://your-production-url.com',  // Production

  timeout: 30000,  // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  }
};

// Create axios instance
const apiClient = axios.create(API_CONFIG);

// Request interceptor - add auth token
apiClient.interceptors.request.use(
  async (config) => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (error) {
      console.error('Error getting auth token:', error);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle errors
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired - logout user
      await AsyncStorage.removeItem('authToken');
      await AsyncStorage.removeItem('user');
      // Navigate to login (handle in your navigation)
    }
    return Promise.reject(error);
  }
);

// ==================== AUTH API ====================

export const authAPI = {
  /**
   * Login user
   */
  login: async (username, password) => {
    try {
      const response = await apiClient.post('/login', {
        username,
        password
      });

      if (response.data.token) {
        await AsyncStorage.setItem('authToken', response.data.token);
        await AsyncStorage.setItem('user', JSON.stringify(response.data.user));
      }

      return response.data;
    } catch (error) {
      throw handleAPIError(error);
    }
  },

  /**
   * Register new user
   */
  register: async (username, password, confirmPassword) => {
    try {
      const response = await apiClient.post('/register', {
        username,
        password,
        confirm_password: confirmPassword
      });

      return response.data;
    } catch (error) {
      throw handleAPIError(error);
    }
  },

  /**
   * Logout user
   */
  logout: async () => {
    try {
      await apiClient.post('/logout');
      await AsyncStorage.removeItem('authToken');
      await AsyncStorage.removeItem('user');
    } catch (error) {
      // Still clear local storage even if API call fails
      await AsyncStorage.removeItem('authToken');
      await AsyncStorage.removeItem('user');
      throw handleAPIError(error);
    }
  },

  /**
   * Get current user
   */
  getCurrentUser: async () => {
    try {
      const userStr = await AsyncStorage.getItem('user');
      return userStr ? JSON.parse(userStr) : null;
    } catch (error) {
      return null;
    }
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated: async () => {
    const token = await AsyncStorage.getItem('authToken');
    return !!token;
  }
};

// ==================== TTS API ====================

export const ttsAPI = {
  /**
   * Generate TTS audio
   */
  generate: async (text, voice = 'alloy', speed = 1.0) => {
    try {
      const response = await apiClient.post('/api/tts', {
        text,
        voice,
        speed
      });

      return response.data;
    } catch (error) {
      throw handleAPIError(error);
    }
  },

  /**
   * Download TTS audio file
   */
  downloadAudio: async (audioUrl, filename) => {
    try {
      const fileUri = `${FileSystem.documentDirectory}${filename}`;

      const downloadResult = await FileSystem.downloadAsync(
        audioUrl,
        fileUri
      );

      return downloadResult.uri;
    } catch (error) {
      throw new Error(`Download failed: ${error.message}`);
    }
  },

  /**
   * Get available voices
   */
  getVoices: async () => {
    try {
      const response = await apiClient.get('/api/voices');
      return response.data.voices || [
        'alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'
      ];
    } catch (error) {
      // Return default voices if API fails
      return ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'];
    }
  }
};

// ==================== AI AGENTS API ====================

export const aiAPI = {
  /**
   * Preprocess text with AI
   */
  preprocess: async (text) => {
    try {
      const response = await apiClient.post('/api/agent/preprocess', {
        text
      });

      return response.data.processed_text || response.data.result;
    } catch (error) {
      throw handleAPIError(error);
    }
  },

  /**
   * Smart chunk long text
   */
  chunk: async (text) => {
    try {
      const response = await apiClient.post('/api/agent/smart-chunk', {
        text
      });

      return response.data.chunks || response.data.result;
    } catch (error) {
      throw handleAPIError(error);
    }
  },

  /**
   * Get metadata suggestions
   */
  suggestMetadata: async (text) => {
    try {
      const response = await apiClient.post('/api/agent/suggest-metadata', {
        text
      });

      return response.data;
    } catch (error) {
      throw handleAPIError(error);
    }
  },

  /**
   * Analyze text quality for TTS
   */
  analyze: async (text) => {
    try {
      const response = await apiClient.post('/api/agent/analyze', {
        text
      });

      return response.data;
    } catch (error) {
      throw handleAPIError(error);
    }
  },

  /**
   * Get recommended voice for text
   */
  recommendVoice: async (text) => {
    try {
      const response = await apiClient.post('/api/agent/recommend-voice', {
        text
      });

      return response.data.recommended_voice || 'alloy';
    } catch (error) {
      return 'alloy';  // Default fallback
    }
  }
};

// ==================== AUDIO LIBRARY API ====================

export const libraryAPI = {
  /**
   * Get user's audio files
   */
  getAudioFiles: async () => {
    try {
      const response = await apiClient.get('/api/audio/list');
      return response.data.files || [];
    } catch (error) {
      throw handleAPIError(error);
    }
  },

  /**
   * Delete audio file
   */
  deleteAudioFile: async (fileId) => {
    try {
      const response = await apiClient.delete(`/api/audio/delete/${fileId}`);
      return response.data;
    } catch (error) {
      throw handleAPIError(error);
    }
  },

  /**
   * Get audio file details
   */
  getAudioFileDetails: async (fileId) => {
    try {
      const response = await apiClient.get(`/api/audio/${fileId}`);
      return response.data;
    } catch (error) {
      throw handleAPIError(error);
    }
  },

  /**
   * Download audio file for offline use
   */
  downloadForOffline: async (audioUrl, filename) => {
    return ttsAPI.downloadAudio(audioUrl, filename);
  }
};

// ==================== FILE UPLOAD API ====================

export const fileAPI = {
  /**
   * Upload PDF/DOCX file for text extraction
   */
  uploadFile: async (fileUri, fileName) => {
    try {
      const formData = new FormData();
      formData.append('file', {
        uri: fileUri,
        type: fileName.endsWith('.pdf') ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        name: fileName
      });

      const response = await apiClient.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      return response.data.text || response.data.extracted_text;
    } catch (error) {
      throw handleAPIError(error);
    }
  },

  /**
   * Extract text from image using OCR (if backend supports it)
   */
  extractTextFromImage: async (imageUri) => {
    try {
      const formData = new FormData();
      formData.append('image', {
        uri: imageUri,
        type: 'image/jpeg',
        name: 'photo.jpg'
      });

      const response = await apiClient.post('/api/ocr', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      return response.data.text;
    } catch (error) {
      throw handleAPIError(error);
    }
  }
};

// ==================== ANALYTICS API ====================

export const analyticsAPI = {
  /**
   * Log analytics event
   */
  logEvent: async (eventName, eventData) => {
    try {
      await apiClient.post('/api/analytics/event', {
        event: eventName,
        data: eventData,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      // Silent fail for analytics
      console.debug('Analytics error:', error);
    }
  }
};

// ==================== HELPER FUNCTIONS ====================

/**
 * Handle API errors and return user-friendly messages
 */
function handleAPIError(error) {
  if (error.response) {
    // Server responded with error
    const message = error.response.data?.error || error.response.data?.message || 'An error occurred';
    return new Error(message);
  } else if (error.request) {
    // Request made but no response
    return new Error('No response from server. Check your internet connection.');
  } else {
    // Error in request setup
    return new Error(error.message || 'An unexpected error occurred');
  }
}

/**
 * Check API connectivity
 */
export async function checkAPIConnection() {
  try {
    const response = await apiClient.get('/api/health');
    return response.status === 200;
  } catch (error) {
    return false;
  }
}

/**
 * Get API base URL (useful for constructing audio URLs)
 */
export function getAPIBaseURL() {
  return API_CONFIG.baseURL;
}

// Export default API object
export default {
  auth: authAPI,
  tts: ttsAPI,
  ai: aiAPI,
  library: libraryAPI,
  file: fileAPI,
  analytics: analyticsAPI,
  checkConnection: checkAPIConnection,
  getBaseURL: getAPIBaseURL
};
