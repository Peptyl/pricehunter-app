// Profile Screen - User profile and settings
import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Switch } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';

import type { RootStackParamList } from '../types';
import { theme } from '../theme';
import { useAppSelector, useAppDispatch } from '../store/hooks';
import { setDarkMode, setNotificationsEnabled, setPriceAlertThreshold } from '../store/slices/userSlice';

interface SettingItemProps {
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  subtitle?: string;
  onPress?: () => void;
  rightElement?: React.ReactNode;
}

const SettingItem: React.FC<SettingItemProps> = ({ icon, title, subtitle, onPress, rightElement }) => (
  <TouchableOpacity style={styles.settingItem} onPress={onPress} disabled={!onPress}>
    <View style={styles.settingIcon}>
      <Ionicons name={icon} size={22} color={theme.colors.primary} />
    </View>
    <View style={styles.settingContent}>
      <Text style={styles.settingTitle}>{title}</Text>
      {subtitle && <Text style={styles.settingSubtitle}>{subtitle}</Text>}
    </View>
    {rightElement}
  </TouchableOpacity>
);

export const ProfileScreen: React.FC = () => {
  const navigation = useNavigation<StackNavigationProp<RootStackParamList>>();
  const dispatch = useAppDispatch();
  const { preferences, isAuthenticated, email } = useAppSelector((state) => state.user);

  const handleToggleDarkMode = (value: boolean) => {
    dispatch(setDarkMode(value));
  };

  const handleToggleNotifications = (value: boolean) => {
    dispatch(setNotificationsEnabled(value));
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" />
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.avatar}>
            <Ionicons name="person" size={48} color={theme.colors.text} />
          </View>
          <Text style={styles.name}>
            {isAuthenticated ? email : 'Guest User'}
          </Text>
          <Text style={styles.status}>
            {isAuthenticated ? 'Premium Member' : 'Sign in to save alerts'}
          </Text>
          
          {!isAuthenticated && (
            <TouchableOpacity style={styles.signInButton}>
              <Text style={styles.signInText}>Sign In</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Stats */}
        <View style={styles.statsContainer}>
          <View style={styles.stat}>
            <Text style={styles.statValue}>12</Text>
            <Text style={styles.statLabel}>Active Alerts</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.stat}>
            <Text style={styles.statValue}>5</Text>
            <Text style={styles.statLabel}>Deals Found</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.stat}>
            <Text style={styles.statValue}>£124</Text>
            <Text style={styles.statLabel}>Total Saved</Text>
          </View>
        </View>

        {/* Preferences */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Preferences</Text>
          
          <SettingItem
            icon="moon-outline"
            title="Dark Mode"
            subtitle="Use dark theme throughout the app"
            rightElement={
              <Switch
                value={preferences.darkMode}
                onValueChange={handleToggleDarkMode}
                trackColor={{ false: theme.colors.surfaceVariant, true: theme.colors.primary }}
                thumbColor={preferences.darkMode ? theme.colors.text : theme.colors.textMuted}
              />
            }
          />
          
          <SettingItem
            icon="notifications-outline"
            title="Push Notifications"
            subtitle="Get notified about new deals"
            rightElement={
              <Switch
                value={preferences.notificationsEnabled}
                onValueChange={handleToggleNotifications}
                trackColor={{ false: theme.colors.surfaceVariant, true: theme.colors.primary }}
                thumbColor={preferences.notificationsEnabled ? theme.colors.text : theme.colors.textMuted}
              />
            }
          />
        </View>

        {/* Account */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Account</Text>
          
          <SettingItem
            icon="bookmark-outline"
            title="Saved Perfumes"
            subtitle="Your watchlist"
            onPress={() => {}}
            rightElement={<Ionicons name="chevron-forward" size={20} color={theme.colors.textMuted} />}
          />
          
          <SettingItem
            icon="time-outline"
            title="Deal History"
            subtitle="Past deals you've viewed"
            onPress={() => {}}
            rightElement={<Ionicons name="chevron-forward" size={20} color={theme.colors.textMuted} />}
          />
          
          <SettingItem
            icon="settings-outline"
            title="Settings"
            subtitle="App preferences and account"
            onPress={() => navigation.navigate('Settings')}
            rightElement={<Ionicons name="chevron-forward" size={20} color={theme.colors.textMuted} />}
          />
        </View>

        {/* About */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>About</Text>
          
          <SettingItem
            icon="help-circle-outline"
            title="Help & Support"
            onPress={() => {}}
            rightElement={<Ionicons name="chevron-forward" size={20} color={theme.colors.textMuted} />}
          />
          
          <SettingItem
            icon="document-text-outline"
            title="Privacy Policy"
            onPress={() => {}}
            rightElement={<Ionicons name="chevron-forward" size={20} color={theme.colors.textMuted} />}
          />
          
          <SettingItem
            icon="information-circle-outline"
            title="About PriceHunter"
            subtitle="Version 1.0.0"
          />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  header: {
    alignItems: 'center',
    paddingVertical: theme.spacing.xl,
    paddingHorizontal: theme.spacing.md,
  },
  avatar: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: theme.colors.surface,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: theme.spacing.md,
  },
  name: {
    fontSize: 24,
    fontWeight: '700',
    color: theme.colors.text,
  },
  status: {
    fontSize: 14,
    color: theme.colors.textSecondary,
    marginTop: theme.spacing.xs,
  },
  signInButton: {
    backgroundColor: theme.colors.primary,
    paddingHorizontal: theme.spacing.xl,
    paddingVertical: theme.spacing.md,
    borderRadius: theme.borderRadius.md,
    marginTop: theme.spacing.lg,
  },
  signInText: {
    color: theme.colors.text,
    fontSize: 16,
    fontWeight: '600',
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: theme.spacing.lg,
    marginHorizontal: theme.spacing.md,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.lg,
    marginBottom: theme.spacing.lg,
  },
  stat: {
    flex: 1,
    alignItems: 'center',
  },
  statDivider: {
    width: 1,
    height: 40,
    backgroundColor: theme.colors.border,
  },
  statValue: {
    fontSize: 24,
    fontWeight: '700',
    color: theme.colors.primary,
  },
  statLabel: {
    fontSize: 12,
    color: theme.colors.textSecondary,
    marginTop: 4,
  },
  section: {
    marginBottom: theme.spacing.lg,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.colors.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginHorizontal: theme.spacing.md,
    marginBottom: theme.spacing.sm,
    marginTop: theme.spacing.md,
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.md,
    backgroundColor: theme.colors.surface,
  },
  settingIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: theme.colors.surfaceVariant,
    justifyContent: 'center',
    alignItems: 'center',
  },
  settingContent: {
    flex: 1,
    marginLeft: theme.spacing.md,
  },
  settingTitle: {
    fontSize: 16,
    color: theme.colors.text,
  },
  settingSubtitle: {
    fontSize: 13,
    color: theme.colors.textMuted,
    marginTop: 2,
  },
});

export default ProfileScreen;
