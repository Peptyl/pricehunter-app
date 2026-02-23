// Deal Details Screen
import React from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ScrollView, 
  TouchableOpacity,
  Linking,
  Alert,
} from 'react-native';
import { RouteProp, useRoute } from '@react-navigation/native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

import type { RootStackParamList } from '../types';
import { useGetDealByIdQuery, useCreateAlertMutation } from '../api/priceHunterApi';
import { theme } from '../theme';
import { formatPrice, formatSavings, getDealTemperature } from '../utils';

import ErrorState from '../components/ErrorState';
import { Skeleton } from '../components/Skeleton';

export const DealDetailsScreen: React.FC = () => {
  const route = useRoute<RouteProp<RootStackParamList, 'DealDetails'>>();
  const { dealId } = route.params;
  
  const { data: deal, isLoading, isError, refetch } = useGetDealByIdQuery(dealId);
  const [createAlert] = useCreateAlertMutation();

  const handleBuyNow = async () => {
    if (deal?.retailer_url) {
      const supported = await Linking.canOpenURL(deal.retailer_url);
      if (supported) {
        await Linking.openURL(deal.retailer_url);
      } else {
        Alert.alert('Error', 'Cannot open this link');
      }
    }
  };

  const handleSetAlert = async () => {
    if (!deal) return;
    try {
      await createAlert({
        perfumeId: deal.perfume_id,
        targetPrice: deal.best_price * 0.95, // 5% lower than current
      }).unwrap();
      Alert.alert('Success', 'Price alert set!');
    } catch (error) {
      Alert.alert('Error', 'Failed to set alert');
    }
  };

  if (isLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="light" />
        <View style={styles.loadingContainer}>
          <Skeleton width="100%" height={200} borderRadius={theme.borderRadius.lg} />
          <Skeleton width="70%" height={24} style={{ marginTop: theme.spacing.lg }} />
          <Skeleton width="50%" height={16} style={{ marginTop: theme.spacing.md }} />
          <Skeleton width="100%" height={48} style={{ marginTop: theme.spacing.xl }} />
        </View>
      </SafeAreaView>
    );
  }

  if (isError || !deal) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="light" />
        <ErrorState onRetry={refetch} />
      </SafeAreaView>
    );
  }

  const temperature = getDealTemperature(deal.savings_percent);
  const tempColor = 
    temperature === 'hot' ? theme.colors.dealHot :
    temperature === 'good' ? theme.colors.dealGood :
    theme.colors.dealMild;

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" />
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Image Placeholder */}
        <View style={styles.imageContainer}>
          <View style={styles.imagePlaceholder}>
            <Ionicons name="image" size={64} color={theme.colors.textMuted} />
          </View>
          <View style={[styles.tempBadge, { backgroundColor: tempColor }]}>
            <Text style={styles.tempText}>
              {temperature === 'hot' ? '🔥 HOT' : temperature === 'good' ? '✓ GOOD' : 'MILD'}
            </Text>
          </View>
        </View>

        {/* Content */}
        <View style={styles.content}>
          <Text style={styles.brand}>{deal.brand.toUpperCase()}</Text>
          <Text style={styles.name}>{deal.perfume}</Text>

          {/* Price Section */}
          <View style={styles.priceSection}>
            <View style={styles.currentPriceContainer}>
              <Text style={styles.currentPrice}>{formatPrice(deal.best_price)}</Text>
              <Text style={styles.atRetailer}>at {deal.retailer}</Text>
            </View>
            <View style={styles.savingsContainer}>
              <Text style={styles.savingsPercent}>
                {formatSavings(deal.savings_percent)}
              </Text>
              <Text style={styles.savingsAmount}>
                You save {formatPrice(deal.savings)}
              </Text>
            </View>
          </View>

          {/* Retail Price */}
          <View style={styles.retailRow}>
            <Text style={styles.retailLabel}>Typical Retail:</Text>
            <Text style={styles.retailPrice}>{formatPrice(deal.retail_price)}</Text>
          </View>

          {/* Stock Status */}
          <View style={styles.stockRow}>
            <Ionicons 
              name={deal.in_stock ? "checkmark-circle" : "close-circle"} 
              size={20} 
              color={deal.in_stock ? theme.colors.success : theme.colors.error} 
            />
            <Text style={[
              styles.stockText,
              { color: deal.in_stock ? theme.colors.success : theme.colors.error }
            ]}>
              {deal.in_stock ? 'In Stock' : 'Out of Stock'}
            </Text>
          </View>

          {/* Actions */}
          <TouchableOpacity style={styles.buyButton} onPress={handleBuyNow}>
            <Ionicons name="open-outline" size={20} color={theme.colors.text} />
            <Text style={styles.buyButtonText}>Buy at {deal.retailer}</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.alertButton} onPress={handleSetAlert}>
            <Ionicons name="notifications-outline" size={20} color={theme.colors.primary} />
            <Text style={styles.alertButtonText}>Set Price Alert</Text>
          </TouchableOpacity>

          {/* Details */}
          <View style={styles.detailsSection}>
            <Text style={styles.detailsTitle}>Deal Details</Text>
            
            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>Discovered</Text>
              <Text style={styles.detailValue}>
                {new Date(deal.discovered_at).toLocaleDateString('en-GB', {
                  day: 'numeric',
                  month: 'long',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </Text>
            </View>
            
            {deal.size_ml && (
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Size</Text>
                <Text style={styles.detailValue}>{deal.size_ml}ml</Text>
              </View>
            )}
          </View>
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
  loadingContainer: {
    flex: 1,
    padding: theme.spacing.lg,
  },
  imageContainer: {
    height: 250,
    backgroundColor: theme.colors.surface,
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  imagePlaceholder: {
    width: 150,
    height: 150,
    borderRadius: 75,
    backgroundColor: theme.colors.surfaceVariant,
    justifyContent: 'center',
    alignItems: 'center',
  },
  tempBadge: {
    position: 'absolute',
    top: theme.spacing.md,
    right: theme.spacing.md,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.xs,
    borderRadius: theme.borderRadius.sm,
  },
  tempText: {
    color: theme.colors.text,
    fontSize: 12,
    fontWeight: '700',
  },
  content: {
    padding: theme.spacing.lg,
  },
  brand: {
    fontSize: 13,
    fontWeight: '600',
    color: theme.colors.primary,
    letterSpacing: 1,
  },
  name: {
    fontSize: 28,
    fontWeight: '700',
    color: theme.colors.text,
    marginTop: theme.spacing.xs,
    lineHeight: 36,
  },
  priceSection: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginTop: theme.spacing.lg,
    padding: theme.spacing.lg,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.lg,
  },
  currentPriceContainer: {
    flex: 1,
  },
  currentPrice: {
    fontSize: 32,
    fontWeight: '700',
    color: theme.colors.primary,
  },
  atRetailer: {
    fontSize: 14,
    color: theme.colors.textSecondary,
    marginTop: 4,
  },
  savingsContainer: {
    alignItems: 'flex-end',
  },
  savingsPercent: {
    fontSize: 20,
    fontWeight: '700',
    color: theme.colors.success,
  },
  savingsAmount: {
    fontSize: 14,
    color: theme.colors.textSecondary,
    marginTop: 4,
  },
  retailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: theme.spacing.md,
  },
  retailLabel: {
    fontSize: 14,
    color: theme.colors.textSecondary,
  },
  retailPrice: {
    fontSize: 14,
    color: theme.colors.textMuted,
    textDecorationLine: 'line-through',
  },
  stockRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: theme.spacing.md,
  },
  stockText: {
    fontSize: 14,
    fontWeight: '600',
    marginLeft: theme.spacing.sm,
  },
  buyButton: {
    flexDirection: 'row',
    backgroundColor: theme.colors.primary,
    padding: theme.spacing.lg,
    borderRadius: theme.borderRadius.md,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: theme.spacing.xl,
    gap: theme.spacing.sm,
  },
  buyButtonText: {
    color: theme.colors.text,
    fontSize: 16,
    fontWeight: '600',
  },
  alertButton: {
    flexDirection: 'row',
    backgroundColor: theme.colors.surface,
    padding: theme.spacing.lg,
    borderRadius: theme.borderRadius.md,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: theme.spacing.md,
    borderWidth: 1,
    borderColor: theme.colors.primary,
    gap: theme.spacing.sm,
  },
  alertButtonText: {
    color: theme.colors.primary,
    fontSize: 16,
    fontWeight: '600',
  },
  detailsSection: {
    marginTop: theme.spacing.xl,
    paddingTop: theme.spacing.lg,
    borderTopWidth: 1,
    borderTopColor: theme.colors.border,
  },
  detailsTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: theme.colors.text,
    marginBottom: theme.spacing.md,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: theme.spacing.sm,
  },
  detailLabel: {
    fontSize: 14,
    color: theme.colors.textSecondary,
  },
  detailValue: {
    fontSize: 14,
    color: theme.colors.text,
    fontWeight: '500',
  },
});

export default DealDetailsScreen;
