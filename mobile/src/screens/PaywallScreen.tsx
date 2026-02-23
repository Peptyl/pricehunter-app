// Paywall Screen - Pro subscription upgrade
import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';

import { theme } from '../theme';
import { useRevenueCat } from '../hooks/useRevenueCat';
import { useAnalytics } from '../hooks/useAnalytics';
import type { RootStackParamList } from '../types';

type PaywallNavigationProp = StackNavigationProp<RootStackParamList>;

const PRO_FEATURES = [
  { icon: 'notifications', title: 'Unlimited Alerts', description: 'Set price alerts for unlimited perfumes' },
  { icon: 'time', title: 'Early Access', description: 'Get deals 2 hours before free users' },
  { icon: 'trending-up', title: 'Price History', description: 'View 12-month price charts' },
  { icon: 'bookmark', title: 'Saved Searches', description: 'Save and get notified on custom searches' },
  { icon: 'close-circle', title: 'No Ads', description: 'Enjoy an ad-free experience' },
];

export const PaywallScreen: React.FC = () => {
  const navigation = useNavigation<PaywallNavigationProp>();
  const { 
    isLoading, 
    isPro, 
    offerings, 
    purchasePackage, 
    restorePurchases,
    error,
    getProPackage,
  } = useRevenueCat();
  const { logEvent, logPurchase } = useAnalytics();

  const handlePurchase = async (annual: boolean = false) => {
    const pack = getProPackage(annual);
    if (!pack) {
      Alert.alert('Error', 'No subscription available at this time');
      return;
    }

    logEvent('purchase_initiated', { 
      product: pack.identifier,
      price: pack.product.price,
    });

    const success = await purchasePackage(pack);
    
    if (success) {
      logPurchase({
        transactionId: pack.identifier,
        value: pack.product.price,
        currency: pack.product.currencyCode || 'GBP',
        itemName: 'Pro Subscription',
      });
      logEvent('purchase_completed', { product: pack.identifier });
      Alert.alert('Success!', 'You are now a Pro member!', [
        { text: 'Awesome!', onPress: () => navigation.goBack() },
      ]);
    }
  };

  const handleRestore = async () => {
    const restored = await restorePurchases();
    if (restored) {
      Alert.alert('Success!', 'Your purchases have been restored.', [
        { text: 'Great!', onPress: () => navigation.goBack() },
      ]);
    } else {
      Alert.alert('No Purchases Found', 'No previous purchases were found.');
    }
  };

  if (isPro) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.proMemberContainer}>
          <View style={styles.proBadge}>
            <Ionicons name="star" size={48} color={theme.colors.primary} />
          </View>
          <Text style={styles.proTitle}>You're a Pro Member!</Text>
          <Text style={styles.proSubtitle}>
            Thanks for supporting PriceHunter. You have access to all premium features.
          </Text>
          <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
            <Text style={styles.backButtonText}>Back to App</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const monthlyPackage = getProPackage(false);
  const annualPackage = getProPackage(true);

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.closeButton} onPress={() => navigation.goBack()}>
            <Ionicons name="close" size={28} color={theme.colors.text} />
          </TouchableOpacity>
          <View style={styles.logoContainer}>
            <Ionicons name="flame" size={48} color={theme.colors.primary} />
          </View>
          <Text style={styles.title}>Upgrade to Pro</Text>
          <Text style={styles.subtitle}>Unlock the full power of PriceHunter</Text>
        </View>

        {/* Features */}
        <View style={styles.featuresContainer}>
          {PRO_FEATURES.map((feature, index) => (
            <View key={index} style={styles.featureItem}>
              <View style={styles.featureIcon}>
                <Ionicons name={feature.icon as any} size={24} color={theme.colors.primary} />
              </View>
              <View style={styles.featureContent}>
                <Text style={styles.featureTitle}>{feature.title}</Text>
                <Text style={styles.featureDescription}>{feature.description}</Text>
              </View>
            </View>
          ))}
        </View>

        {/* Pricing Options */}
        <View style={styles.pricingContainer}>
          {annualPackage && (
            <TouchableOpacity 
              style={[styles.pricingCard, styles.annualCard]} 
              onPress={() => handlePurchase(true)}
              disabled={isLoading}
            >
              <View style={styles.bestValueBadge}>
                <Text style={styles.bestValueText}>BEST VALUE</Text>
              </View>
              <Text style={styles.pricingPeriod}>Annual</Text>
              <Text style={styles.pricingPrice}>
                {annualPackage.product.priceString}
                <Text style={styles.pricingPeriodSuffix}>/year</Text>
              </Text>
              <Text style={styles.pricingDescription}>
                Save 40% vs monthly
              </Text>
            </TouchableOpacity>
          )}

          {monthlyPackage && (
            <TouchableOpacity 
              style={styles.pricingCard} 
              onPress={() => handlePurchase(false)}
              disabled={isLoading}
            >
              <Text style={styles.pricingPeriod}>Monthly</Text>
              <Text style={styles.pricingPrice}>
                {monthlyPackage.product.priceString}
                <Text style={styles.pricingPeriodSuffix}>/month</Text>
              </Text>
              <Text style={styles.pricingDescription}>
                Flexible, cancel anytime
              </Text>
            </TouchableOpacity>
          )}
        </View>

        {isLoading && (
          <ActivityIndicator color={theme.colors.primary} style={styles.loader} />
        )}

        {error && (
          <Text style={styles.errorText}>{error}</Text>
        )}

        {/* Restore Purchases */}
        <TouchableOpacity style={styles.restoreButton} onPress={handleRestore} disabled={isLoading}>
          <Text style={styles.restoreText}>Restore Purchases</Text>
        </TouchableOpacity>

        {/* Terms */}
        <Text style={styles.termsText}>
          Payment will be charged to your account. Subscriptions automatically renew unless
          auto-renew is turned off at least 24 hours before the end of the current period.
        </Text>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  scrollContent: {
    padding: theme.spacing.lg,
  },
  header: {
    alignItems: 'center',
    marginBottom: theme.spacing.xl,
  },
  closeButton: {
    position: 'absolute',
    top: 0,
    right: 0,
    padding: theme.spacing.sm,
  },
  logoContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: theme.colors.surface,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: theme.spacing.lg,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: theme.colors.text,
    marginBottom: theme.spacing.sm,
  },
  subtitle: {
    fontSize: 16,
    color: theme.colors.textSecondary,
  },
  featuresContainer: {
    marginBottom: theme.spacing.xl,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: theme.spacing.md,
  },
  featureIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: theme.colors.surfaceVariant,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: theme.spacing.md,
  },
  featureContent: {
    flex: 1,
  },
  featureTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.text,
    marginBottom: 2,
  },
  featureDescription: {
    fontSize: 14,
    color: theme.colors.textSecondary,
  },
  pricingContainer: {
    flexDirection: 'row',
    gap: theme.spacing.md,
    marginBottom: theme.spacing.xl,
  },
  pricingCard: {
    flex: 1,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.lg,
    padding: theme.spacing.lg,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: theme.colors.border,
  },
  annualCard: {
    borderColor: theme.colors.primary,
    position: 'relative',
  },
  bestValueBadge: {
    position: 'absolute',
    top: -12,
    backgroundColor: theme.colors.primary,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.xs,
    borderRadius: theme.borderRadius.sm,
  },
  bestValueText: {
    color: theme.colors.text,
    fontSize: 12,
    fontWeight: '700',
  },
  pricingPeriod: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.text,
    marginBottom: theme.spacing.sm,
  },
  pricingPrice: {
    fontSize: 28,
    fontWeight: '700',
    color: theme.colors.primary,
    marginBottom: theme.spacing.sm,
  },
  pricingPeriodSuffix: {
    fontSize: 14,
    fontWeight: '400',
    color: theme.colors.textSecondary,
  },
  pricingDescription: {
    fontSize: 12,
    color: theme.colors.textMuted,
    textAlign: 'center',
  },
  loader: {
    marginBottom: theme.spacing.lg,
  },
  errorText: {
    color: theme.colors.error,
    textAlign: 'center',
    marginBottom: theme.spacing.lg,
  },
  restoreButton: {
    alignItems: 'center',
    paddingVertical: theme.spacing.md,
  },
  restoreText: {
    color: theme.colors.primary,
    fontSize: 14,
    fontWeight: '600',
  },
  termsText: {
    fontSize: 11,
    color: theme.colors.textMuted,
    textAlign: 'center',
    marginTop: theme.spacing.lg,
    lineHeight: 16,
  },
  proMemberContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: theme.spacing.xl,
  },
  proBadge: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: theme.colors.surface,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: theme.spacing.lg,
  },
  proTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: theme.colors.text,
    marginBottom: theme.spacing.sm,
  },
  proSubtitle: {
    fontSize: 16,
    color: theme.colors.textSecondary,
    textAlign: 'center',
    marginBottom: theme.spacing.xl,
  },
  backButton: {
    backgroundColor: theme.colors.primary,
    paddingHorizontal: theme.spacing.xl,
    paddingVertical: theme.spacing.md,
    borderRadius: theme.borderRadius.md,
  },
  backButtonText: {
    color: theme.colors.text,
    fontSize: 16,
    fontWeight: '600',
  },
});

export default PaywallScreen;
