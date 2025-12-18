/**
 * VoiceVerse Mobile App
 * Main application entry point
 */

import React, { useState, useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { StatusBar } from 'expo-status-bar';
import { authAPI } from './services/api';

// Screens
import LoginScreen from './screens/LoginScreen';
import RegisterScreen from './screens/RegisterScreen';
import TTSScreen from './screens/TTSScreen';
import LibraryScreen from './screens/LibraryScreen';
import SettingsScreen from './screens/SettingsScreen';

// Components
import LoadingScreen from './components/LoadingScreen';

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

// Theme colors (Spotify-inspired)
const THEME = {
  primary: '#1DB954',
  background: '#191414',
  surface: '#282828',
  text: '#ffffff',
  textSecondary: '#b3b3b3',
};

/**
 * Main Tab Navigator (Authenticated users)
 */
function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={{
        tabBarStyle: {
          backgroundColor: THEME.background,
          borderTopColor: THEME.surface,
        },
        tabBarActiveTintColor: THEME.primary,
        tabBarInactiveTintColor: THEME.textSecondary,
        headerStyle: {
          backgroundColor: THEME.background,
        },
        headerTintColor: THEME.text,
        headerShadowVisible: false,
      }}
    >
      <Tab.Screen
        name="Generate"
        component={TTSScreen}
        options={{
          tabBarIcon: ({ color, size }) => '🎙️',
          title: 'Generate Speech'
        }}
      />
      <Tab.Screen
        name="Library"
        component={LibraryScreen}
        options={{
          tabBarIcon: ({ color, size }) => '📚',
          title: 'Audio Library'
        }}
      />
      <Tab.Screen
        name="Settings"
        component={SettingsScreen}
        options={{
          tabBarIcon: ({ color, size }) => '⚙️',
          title: 'Settings'
        }}
      />
    </Tab.Navigator>
  );
}

/**
 * Main App Component
 */
export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Check authentication status on app start
  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const authenticated = await authAPI.isAuthenticated();
      setIsAuthenticated(authenticated);
    } catch (error) {
      console.error('Auth check error:', error);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle successful login
  const handleLogin = () => {
    setIsAuthenticated(true);
  };

  // Handle logout
  const handleLogout = async () => {
    try {
      await authAPI.logout();
      setIsAuthenticated(false);
    } catch (error) {
      console.error('Logout error:', error);
      setIsAuthenticated(false);
    }
  };

  if (isLoading) {
    return <LoadingScreen />;
  }

  return (
    <>
      <StatusBar style="light" />
      <NavigationContainer>
        <Stack.Navigator
          screenOptions={{
            headerShown: false,
            cardStyle: { backgroundColor: THEME.background },
          }}
        >
          {isAuthenticated ? (
            // Authenticated stack
            <Stack.Screen name="Main">
              {(props) => <MainTabs {...props} onLogout={handleLogout} />}
            </Stack.Screen>
          ) : (
            // Authentication stack
            <>
              <Stack.Screen name="Login">
                {(props) => <LoginScreen {...props} onLoginSuccess={handleLogin} />}
              </Stack.Screen>
              <Stack.Screen name="Register" component={RegisterScreen} />
            </>
          )}
        </Stack.Navigator>
      </NavigationContainer>
    </>
  );
}
