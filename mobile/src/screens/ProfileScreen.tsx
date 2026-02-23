// Profile Screen - User profile with Clerk auth and RevenueCat integration
import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Switch, Alert } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { useUser, useAuth, useClerk } from '@clerk/clerk-expo';

import type { AppStackParamList } from '../types';
import { theme } from '../theme';
import { useAppSelector, useAppDispatch } from '../store/hooks';
import { setDarkMode, setNotificationsEnabled } from '../store/slices/userSlice';
import { useRevenueCat } from '../hooks/useRevenueCat';
import { useAnalytics } from '../hooks/useAnalytics';

type ProfileNavigationProp = StackNavigationProp<AppStackParamList>;

interface SettingItemProps {
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  subtitle?: string;
  onPress?: () => void;
  rightElement?: React.ReactNode;
  isPremium?: boolean;
}

const SettingItem: React.FC<SettingItemProps> = ({ 
  icon, 
  title, 
  subtitle, 
  onPress, 
  rightElement,
  isPremium 
}) => (
  <TouchableOpacity style={styles.settingItem} onPress={onPress} disabled={!onPress}>
    <View style={styles.settingIcon}>
      <Ionicons name={icon} size={22} color={isPremium ? theme.colors.primary : theme.colors.primary} />
    </View>
    <View style={styles.settingContent}>
      <Text style={styles.settingTitle}>{title}</Text>
      {subtitle && <Text style={styles.settingSubtitle}>{subtitle}</Text>}
    </View>
    {isPremium && (
      <View style={styles.premiumBadge}>
        <Text style={styles.premiumBadgeText}>PRO</Text>
      </View>
    )}
    {rightElement}
  </TouchableOpacity>
);

export const ProfileScreen: React.FC = () => {
  const navigation = useNavigation<ProfileNavigationProp>();
  const dispatch = useAppDispatch();
  const { user, isSignedIn } = useUser();
  const { signOut } = useClerk();
  const { isPro } = useRevenueCat();
  const { logEvent } = useAnalytics();
  
  const { preferences } = useAppSelector((state) => state.user);

  const handleToggleDarkMode = (value: boolean) => {
    dispatch(setDarkMode(value));
    logEvent('settings_changed', { setting: 'dark_mode', value });
  };

  const handleToggleNotifications = (value: boolean) => {
    dispatch(setNotificationsEnabled(value));
    logEvent('settings_changed', { setting: 'notifications', value });
  };

  const handleSignOut = async () => {
    Alert.alert(
      'Sign Out',
      'Are you sure you want to sign out?',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Sign Out', 
          style: 'destructive',
          onPress: async () => {
            try {
              await signOut();
              logEvent('logout');
            } catch (error) {
              console.error('Sign out error:', error);
            }
          }
        },
      ]
    );
  };

  const handleUpgrade = () => {
    logEvent('upgrade_prompt_shown', { source: 'profile' });
    navigation.navigate('Paywall');
  };

  // Get user's display info
  const displayName = user?.firstName || user?.emailAddresses[0]?.emailAddress?.split('@')[0] || 'User';
  const email = user?.emailAddresses[0]?.emailAddress || '';
  const avatarUrl = user?.imageUrl;

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" />
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.avatar}>
            {avatarUrl ? (
              <Image source={{ uri: avatarUrl }} style={styles.avatarImage} />
            ) : (
              <Ionicons name="person" size={48} color={theme.colors.text} />
            )}
          </View>
          <Text style={styles.name}>{displayName}</Text>
          <Text style={styles.email}>{email}</Text>
          
          {isPro ? (
            <View style={styles.proBadge}>
              <Ionicons name="star" size={14} color={theme.colors.text} />
              <Text style={styles.proText}>Pro Member</Text>
            </View>
          ) : (
            <TouchableOpacity style={styles.upgradeButton} onPress={handleUpgrade}>
              <Ionicons name="star-outline" size={16} color={theme.colors.text} />
              <Text style={styles.upgradeText}>Upgrade to Pro</Text>
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

        {/* Pro Features (if not Pro) */}
        {!isPro && (
          <View style={styles.proPrompt}>
            <View style={styles.proPromptHeader}>
              <Ionicons name="flame" size={24} color={theme.colors.primary} />
              <Text style={styles.proPromptTitle}>Unlock Pro Features</Text>
            </View>
            <Text style={styles.proPromptText}>
              Get unlimited alerts, early access to deals, and detailed price history
            </Text>
            <TouchableOpacity style={styles.proPromptButton} onPress={handleUpgrade}>
              <Text style={styles.proPromptButtonText}>Upgrade Now</Text>
            </TouchableOpacity>
          </View>
        )}

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
            onPress={() => logEvent('view_deal_history')}
            rightElement={<Ionicons name="chevron-forward" size={20} color={theme.colors.textMuted} />}
          />
          
          <SettingItem
            icon="settings-outline"
            title="Settings"
            subtitle="App preferences and account"
            onPress={() => navigation.navigate('Settings')}
            rightElement={<Ionicons name="chevron-forward" size={20} color={theme.colors.textMuted} />}
          />

          {isPro && (
            <SettingItem
              icon="star"
              title="Pro Membership"
              subtitle="Manage your subscription"
              isPremium
              onPress={() => {}}
              rightElement={<Ionicons name="chevron-forward" size={20} color={theme.colors.textMuted} />}
            />
          )}
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

        {/* Sign Out */}
        {isSignedIn && (
          <View style={styles.section}>
            <TouchableOpacity style={styles.signOutButton} onPress={handleSignOut}>
              <Ionicons name="log-out-outline" size={22} color={theme.colors.error} />
              <Text style={styles.signOutText}>Sign Out</Text>
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
};

// Need to import Image
import { Image } from 'react-native';

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
    overflow: 'hidden',
  },
  avatarImage: {
    width: 100,
    height: 100,
    borderRadius: 50,
  },
  name: {
    fontSize: 24,
    fontWeight: '700',
    color: theme.colors.text,
  },
  email: {
    fontSize: 14,
    color: theme.colors.textSecondary,
    marginTop: theme.spacing.xs,
  },
  proBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.colors.primary,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
    borderRadius: theme.borderRadius.md,
    marginTop: theme.spacing.md,
    gap: theme.spacing.xs,
  },
  proText: {
    color: theme.colors.text,
    fontSize: 14,
    fontWeight: '600',
  },
  upgradeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.colors.surface,
    borderWidth: 1,
    borderColor: theme.colors.primary,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
    borderRadius: theme.borderRadius.md,
    marginTop: theme.spacing.md,
    gap: theme.spacing.xs,
  },
  upgradeText: {
    color: theme.colors.primary,
    fontSize: 14,
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
  proPrompt: {
    marginHorizontal: theme.spacing.md,
    marginBottom: theme.spacing.lg,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.lg,
    padding: theme.spacing.lg,
    borderWidth: 1,
    borderColor: theme.colors.primary,
  },
  proPromptHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    marginBottom: theme.spacing.sm,
  },
  proPromptTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: theme.colors.text,
  },
  proPromptText: {
    fontSize: 14,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.md,
    lineHeight: 20,
  },
  proPromptButton: {
    backgroundColor: theme.colors.primary,
    paddingVertical: theme.spacing.md,
    borderRadius: theme.borderRadius.md,
    alignItems: 'center',
  },
  proPromptButtonText: {
    color: theme.colors.text,
    fontSize: 16,
    fontWeight: '600',
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
  premiumBadge: {
    backgroundColor: theme.colors.primary,
    paddingHorizontal: theme.spacing.sm,
    paddingVertical: 2,
    borderRadius: theme.borderRadius.sm,
    marginRight: theme.spacing.sm,
  },
  premiumBadgeText: {
    color: theme.colors.text,
    fontSize: 10,
    fontWeight: '700',
  },
  signOutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.md,
    backgroundColor: theme.colors.surface,
  },
  signOutText: {
    marginLeft: theme.spacing.md,
    fontSize: 16,
    color: theme.colors.error,
    fontWeight: '500',
  },
});

export default ProfileScreen;
