// Navigation Configuration with Auth Flow
import React, { useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { useUser, useAuth } from '@clerk/clerk-expo';

import type { AppStackParamList, MainTabParamList, AuthStackParamList } from '../types';

// Auth Screens
import SignInScreen from '../auth/SignInScreen';
import SignUpScreen from '../auth/SignUpScreen';

// Main Screens
import DealsScreen from '../screens/DealsScreen';
import PerfumesScreen from '../screens/PerfumesScreen';
import AlertsScreen from '../screens/AlertsScreen';
import ProfileScreen from '../screens/ProfileScreen';
import DealDetailsScreen from '../screens/DealDetailsScreen';
import PerfumeDetailsScreen from '../screens/PerfumeDetailsScreen';
import SettingsScreen from '../screens/SettingsScreen';
import PaywallScreen from '../screens/PaywallScreen';

import { theme } from '../theme';
import { useAnalytics } from '../hooks/useAnalytics';
import { useRevenueCat } from '../hooks/useRevenueCat';

const Stack = createStackNavigator<AppStackParamList>();
const Tab = createBottomTabNavigator<MainTabParamList>();
const AuthStack = createStackNavigator<AuthStackParamList>();

// Auth Navigator
const AuthNavigator = () => {
  return (
    <AuthStack.Navigator
      screenOptions={{
        headerShown: false,
        cardStyle: { backgroundColor: theme.colors.background },
      }}
    >
      <AuthStack.Screen name="SignIn" component={SignInScreen} />
      <AuthStack.Screen name="SignUp" component={SignUpScreen} />
    </AuthStack.Navigator>
  );
};

// Bottom Tab Navigator for main screens
const MainTabNavigator = () => {
  const { logScreenView } = useAnalytics();

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: theme.colors.textMuted,
        tabBarStyle: {
          backgroundColor: theme.colors.surface,
          borderTopColor: theme.colors.border,
          paddingTop: 8,
          paddingBottom: 8,
          height: 64,
        },
        tabBarLabelStyle: {
          fontSize: 12,
          marginTop: 4,
        },
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: keyof typeof Ionicons.glyphMap = 'home';

          switch (route.name) {
            case 'Deals':
              iconName = focused ? 'flame' : 'flame-outline';
              break;
            case 'Perfumes':
              iconName = focused ? 'search' : 'search-outline';
              break;
            case 'Alerts':
              iconName = focused ? 'notifications' : 'notifications-outline';
              break;
            case 'Profile':
              iconName = focused ? 'person' : 'person-outline';
              break;
          }

          return <Ionicons name={iconName} size={size} color={color} />;
        },
      })}
      screenListeners={{
        focus: (e) => {
          logScreenView(e.target?.split('-')[0] || 'Tab');
        },
      }}
    >
      <Tab.Screen 
        name="Deals" 
        component={DealsScreen}
        options={{ tabBarLabel: 'Deals' }}
      />
      <Tab.Screen 
        name="Perfumes" 
        component={PerfumesScreen}
        options={{ tabBarLabel: 'Browse' }}
      />
      <Tab.Screen 
        name="Alerts" 
        component={AlertsScreen}
        options={{ tabBarLabel: 'Alerts' }}
      />
      <Tab.Screen 
        name="Profile" 
        component={ProfileScreen}
        options={{ tabBarLabel: 'Profile' }}
      />
    </Tab.Navigator>
  );
};

// Root Stack Navigator
export const Navigation = () => {
  const { isSignedIn, userId } = useUser();
  const { isLoaded: authLoaded } = useAuth();
  const { logScreenView, setUserId: setAnalyticsUserId } = useAnalytics();
  const { syncUserId } = useRevenueCat();

  // Sync user ID with analytics and RevenueCat when authenticated
  useEffect(() => {
    if (isSignedIn && userId) {
      setAnalyticsUserId(userId);
      syncUserId(userId);
      logScreenView('App_Launch_Authenticated');
    } else if (authLoaded) {
      setAnalyticsUserId(null);
      logScreenView('App_Launch_Guest');
    }
  }, [isSignedIn, userId, authLoaded, setAnalyticsUserId, syncUserId, logScreenView]);

  // Wait for auth to load
  if (!authLoaded) {
    return null;
  }

  return (
    <NavigationContainer>
      <Stack.Navigator
        screenOptions={{
          headerStyle: {
            backgroundColor: theme.colors.surface,
          },
          headerTintColor: theme.colors.text,
          headerTitleStyle: {
            fontWeight: '600',
          },
          cardStyle: {
            backgroundColor: theme.colors.background,
          },
        }}
      >
        {!isSignedIn ? (
          <Stack.Screen
            name="Auth"
            component={AuthNavigator}
            options={{ headerShown: false }}
          />
        ) : (
          <>
            <Stack.Screen
              name="Main"
              component={MainTabNavigator}
              options={{ headerShown: false }}
            />
            <Stack.Screen
              name="DealDetails"
              component={DealDetailsScreen}
              options={{ title: 'Deal Details' }}
            />
            <Stack.Screen
              name="PerfumeDetails"
              component={PerfumeDetailsScreen}
              options={{ title: 'Perfume Details' }}
            />
            <Stack.Screen
              name="Settings"
              component={SettingsScreen}
              options={{ title: 'Settings' }}
            />
            <Stack.Screen
              name="Paywall"
              component={PaywallScreen}
              options={{ 
                title: 'Upgrade',
                presentation: 'modal',
                headerShown: false,
              }}
            />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default Navigation;
