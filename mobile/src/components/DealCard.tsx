// Deal Card Component
import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Image } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import type { Deal } from '../types';
import { theme } from '../theme';
import { formatPrice, formatSavings, formatRelativeTime, getDealTemperature } from '../utils';

interface DealCardProps {
  deal: Deal;
  onPress?: (deal: Deal) => void;
  onBuyNow?: (deal: Deal) => void;
}

export const DealCard: React.FC<DealCardProps> = ({ deal, onPress, onBuyNow }) => {
  const temperature = getDealTemperature(deal.savings_percent);
  const tempColor = 
    temperature === 'hot' ? theme.colors.dealHot :
    temperature === 'good' ? theme.colors.dealGood :
    theme.colors.dealMild;

  return (
    <TouchableOpacity style={styles.container} onPress={() => onPress?.(deal)}>
      {/* Temperature Indicator */}
      <View style={[styles.tempIndicator, { backgroundColor: tempColor }]} />
      
      <View style={styles.content}>
        {/* Image placeholder */}
        <View style={styles.imageContainer}>
          {deal.image_url ? (
            <Image source={{ uri: deal.image_url }} style={styles.image} />
          ) : (
            <View style={styles.imagePlaceholder}>
              <Ionicons name="image-outline" size={32} color={theme.colors.textMuted} />
            </View>
          )}
        </View>

        {/* Info */}
        <View style={styles.info}>
          <Text style={styles.brand} numberOfLines={1}>
            {deal.brand.toUpperCase()}
          </Text>
          <Text style={styles.name} numberOfLines={2}>
            {deal.perfume}
          </Text>
          
          <View style={styles.priceRow}>
            <Text style={styles.currentPrice}>
              {formatPrice(deal.best_price)}
            </Text>
            <Text style={styles.originalPrice}>
              {formatPrice(deal.retail_price)}
            </Text>
          </View>

          <View style={styles.metaRow}>
            <View style={[styles.savingsBadge, { backgroundColor: tempColor + '20' }]}>
              <Text style={[styles.savingsText, { color: tempColor }]}>
                {formatSavings(deal.savings_percent)}
              </Text>
            </View>
            <Text style={styles.retailer} numberOfLines={1}>
              @ {deal.retailer}
            </Text>
          </View>
        </View>

        {/* Buy Button */}
        <TouchableOpacity 
          style={styles.buyButton}
          onPress={() => onBuyNow?.(deal)}
        >
          <Ionicons name="open-outline" size={20} color={theme.colors.primary} />
        </TouchableOpacity>
      </View>

      {/* Footer */}
      <View style={styles.footer}>
        <Ionicons name="time-outline" size={12} color={theme.colors.textMuted} />
        <Text style={styles.timeText}>
          {formatRelativeTime(deal.discovered_at)}
        </Text>
        {deal.in_stock && (
          <>
            <View style={styles.divider} />
            <Ionicons name="checkmark-circle" size={12} color={theme.colors.success} />
            <Text style={styles.stockText}>In Stock</Text>
          </>
        )}
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.lg,
    marginHorizontal: theme.spacing.md,
    marginVertical: theme.spacing.sm,
    overflow: 'hidden',
    ...theme.shadows.md,
  },
  tempIndicator: {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    width: 4,
  },
  content: {
    flexDirection: 'row',
    padding: theme.spacing.md,
  },
  imageContainer: {
    width: 80,
    height: 80,
    borderRadius: theme.borderRadius.md,
    overflow: 'hidden',
  },
  image: {
    width: '100%',
    height: '100%',
  },
  imagePlaceholder: {
    width: '100%',
    height: '100%',
    backgroundColor: theme.colors.surfaceVariant,
    justifyContent: 'center',
    alignItems: 'center',
  },
  info: {
    flex: 1,
    marginLeft: theme.spacing.md,
    justifyContent: 'center',
  },
  brand: {
    fontSize: 11,
    fontWeight: '600',
    color: theme.colors.primary,
    letterSpacing: 0.5,
  },
  name: {
    fontSize: 15,
    fontWeight: '600',
    color: theme.colors.text,
    marginTop: 2,
    lineHeight: 20,
  },
  priceRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginTop: theme.spacing.sm,
  },
  currentPrice: {
    fontSize: 18,
    fontWeight: '700',
    color: theme.colors.primary,
  },
  originalPrice: {
    fontSize: 13,
    color: theme.colors.textMuted,
    textDecorationLine: 'line-through',
    marginLeft: theme.spacing.sm,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: theme.spacing.sm,
  },
  savingsBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: theme.borderRadius.sm,
  },
  savingsText: {
    fontSize: 11,
    fontWeight: '600',
  },
  retailer: {
    fontSize: 12,
    color: theme.colors.textSecondary,
    marginLeft: theme.spacing.sm,
    flex: 1,
  },
  buyButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
    alignSelf: 'center',
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: theme.spacing.md,
    paddingBottom: theme.spacing.md,
    marginTop: -theme.spacing.sm,
  },
  timeText: {
    fontSize: 11,
    color: theme.colors.textMuted,
    marginLeft: 4,
  },
  divider: {
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: theme.colors.border,
    marginHorizontal: 8,
  },
  stockText: {
    fontSize: 11,
    color: theme.colors.success,
    marginLeft: 4,
  },
});

export default DealCard;
