// PriceHunter Mobile App - Main Entry Point
import React, { useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { Provider as ReduxProvider } from 'react-redux';
import { PaperProvider } from 'react-native-paper';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import analytics from '@react-native-firebase/analytics';

import { store } from './src/store';
import Navigation from './src/navigation';
import { theme } from './src/theme';
import { AuthProvider } from './src/auth/AuthProvider';

// React Native Paper theme configuration
const paperTheme = {
  colors: {
    primary: theme.colors.primary,
    onPrimary: theme.colors.text,
    primaryContainer: theme.colors.surface,
    onPrimaryContainer: theme.colors.text,
    secondary: theme.colors.primary,
    onSecondary: theme.colors.text,
    secondaryContainer: theme.colors.surface,
    onSecondaryContainer: theme.colors.text,
    tertiary: theme.colors.accent,
    onTertiary: theme.colors.text,
    tertiaryContainer: theme.colors.surface,
    onTertiaryContainer: theme.colors.text,
    error: theme.colors.error,
    onError: theme.colors.text,
    errorContainer: theme.colors.surface,
    onErrorContainer: theme.colors.text,
    background: theme.colors.background,
    onBackground: theme.colors.text,
    surface: theme.colors.surface,
    onSurface: theme.colors.text,
    surfaceVariant: theme.colors.surfaceVariant,
    onSurfaceVariant: theme.colors.textSecondary,
    outline: theme.colors.border,
    outlineVariant: theme.colors.divider,
    shadow: '#000',
    scrim: theme.colors.overlay,
    inverseSurface: theme.colors.text,
    inverseOnSurface: theme.colors.background,
    inversePrimary: theme.colors.primary,
    elevation: {
      level0: 'transparent',
      level1: theme.colors.surface,
      level2: theme.colors.surface,
      level3: theme.colors.surface,
      level4: theme.colors.surface,
      level5: theme.colors.surface,
    },
    surfaceDisabled: theme.colors.surfaceVariant,
    onSurfaceDisabled: theme.colors.textMuted,
    backdrop: theme.colors.overlay,
  },
};

// App initialization
const AppInitializer: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  useEffect(() => {
    // Log app open event
    const logAppOpen = async () => {
      try {
        await analytics().logEvent('app_open');
        console.log('[Analytics] App open event logged');
      } catch (error) {
        console.error('[Analytics] Failed to log app open:', error);
      }
    };

    logAppOpen();
  }, []);

  return <>{children}</>;
};

export default function App() {
  return (
    <ReduxProvider store={store}>
      <AuthProvider>
        <PaperProvider theme={paperTheme}>
          <SafeAreaProvider>
            <AppInitializer>
              <Navigation />
              <StatusBar style="light" />
            </AppInitializer>
          </SafeAreaProvider>
        </PaperProvider>
      </AuthProvider>
    </ReduxProvider>
  );
}
