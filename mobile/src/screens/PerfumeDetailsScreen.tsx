// Perfume Details Screen
import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { RouteProp, useRoute } from '@react-navigation/native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

import type { RootStackParamList } from '../types';
import { useGetPerfumeByIdQuery } from '../api/priceHunterApi';
import { theme } from '../theme';
import { formatPrice } from '../utils';

import ErrorState from '../components/ErrorState';
import { Skeleton } from '../components/Skeleton';

export const PerfumeDetailsScreen: React.FC = () => {
  const route = useRoute<RouteProp<RootStackParamList, 'PerfumeDetails'>>();
  const { perfumeId } = route.params;
  
  const { data: perfume, isLoading, isError, refetch } = useGetPerfumeByIdQuery(perfumeId);

  if (isLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="light" />
        <View style={styles.loadingContainer}>
          <Skeleton width="100%" height={200} borderRadius={theme.borderRadius.lg} />
          <Skeleton width="70%" height={24} style={{ marginTop: theme.spacing.lg }} />
          <Skeleton width="100%" height={100} style={{ marginTop: theme.spacing.md }} />
        </View>
      </SafeAreaView>
    );
  }

  if (isError || !perfume) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="light" />
        <ErrorState onRetry={refetch} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" />
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Image Placeholder */}
        <View style={styles.imageContainer}>
          <View style={styles.imagePlaceholder}>
            <Ionicons name="water" size={64} color={theme.colors.textMuted} />
          </View>
        </View>

        {/* Content */}
        <View style={styles.content}>
          <Text style={styles.house}>{perfume.house || perfume.brand}</Text>
          <Text style={styles.name}>{perfume.name}</Text>

          {perfume.description && (
            <Text style={styles.description}>{perfume.description}</Text>
          )}

          {/* Price Info */}
          <View style={styles.priceSection}>
            <View style={styles.priceRow}>
              <View style={styles.priceItem}>
                <Text style={styles.priceLabel}>Typical Retail</Text>
                <Text style={styles.retailPrice}>
                  {formatPrice(perfume.typical_retail_gbp)}
                </Text>
              </View>
              <View style={styles.priceDivider} />
              <View style={styles.priceItem}>
                <Text style={styles.priceLabel}>Good Deal At</Text>
                <Text style={styles.dealPrice}>
                  {formatPrice(perfume.good_deal_threshold_gbp)}
                </Text>
              </View>
            </View>
          </View>

          {/* Notes */}
          {perfume.notes && perfume.notes.length > 0 && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Fragrance Notes</Text>
              <View style={styles.notesContainer}>
                {perfume.notes.map((note, index) => (
                  <View key={index} style={styles.noteTag}>
                    <Text style={styles.noteText}>{note}</Text>
                  </View>
                ))}
              </View>
            </View>
          )}

          {/* Details */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Details</Text>
            
            {perfume.size_ml && (
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Size</Text>
                <Text style={styles.detailValue}>{perfume.size_ml}ml</Text>
              </View>
            )}
            
            {perfume.concentration && (
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Concentration</Text>
                <Text style={styles.detailValue}>{perfume.concentration}</Text>
              </View>
            )}

            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>Brand</Text>
              <Text style={styles.detailValue}>{perfume.brand}</Text>
            </View>
          </View>

          {/* Actions */}
          <TouchableOpacity style={styles.alertButton}>
            <Ionicons name="notifications-outline" size={20} color={theme.colors.text} />
            <Text style={styles.alertButtonText}>Set Price Alert</Text>
          </TouchableOpacity>
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
  },
  imagePlaceholder: {
    width: 150,
    height: 150,
    borderRadius: 75,
    backgroundColor: theme.colors.surfaceVariant,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    padding: theme.spacing.lg,
  },
  house: {
    fontSize: 14,
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
  description: {
    fontSize: 15,
    color: theme.colors.textSecondary,
    marginTop: theme.spacing.md,
    lineHeight: 22,
  },
  priceSection: {
    marginTop: theme.spacing.lg,
    padding: theme.spacing.lg,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.lg,
  },
  priceRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  priceItem: {
    alignItems: 'center',
  },
  priceLabel: {
    fontSize: 13,
    color: theme.colors.textSecondary,
    marginBottom: 4,
  },
  retailPrice: {
    fontSize: 20,
    fontWeight: '600',
    color: theme.colors.textMuted,
    textDecorationLine: 'line-through',
  },
  dealPrice: {
    fontSize: 24,
    fontWeight: '700',
    color: theme.colors.success,
  },
  priceDivider: {
    width: 1,
    backgroundColor: theme.colors.border,
  },
  section: {
    marginTop: theme.spacing.xl,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: theme.colors.text,
    marginBottom: theme.spacing.md,
  },
  notesContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: theme.spacing.sm,
  },
  noteTag: {
    backgroundColor: theme.colors.surface,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
    borderRadius: theme.borderRadius.round,
  },
  noteText: {
    fontSize: 13,
    color: theme.colors.text,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: theme.spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
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
  alertButton: {
    flexDirection: 'row',
    backgroundColor: theme.colors.primary,
    padding: theme.spacing.lg,
    borderRadius: theme.borderRadius.md,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: theme.spacing.xl,
    marginBottom: theme.spacing.xxl,
    gap: theme.spacing.sm,
  },
  alertButtonText: {
    color: theme.colors.text,
    fontSize: 16,
    fontWeight: '600',
  },
});

export default PerfumeDetailsScreen;
