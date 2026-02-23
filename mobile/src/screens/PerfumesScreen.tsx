// Perfumes Screen - Browse all perfumes
import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TextInput,
  TouchableOpacity,
  ListRenderItem,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

import type { RootStackParamList, Perfume } from '../types';
import { useGetPerfumesQuery } from '../api/priceHunterApi';
import { theme } from '../theme';
import { formatPrice } from '../utils';

import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import { Skeleton } from '../components/Skeleton';

const PerfumeItem: React.FC<{ perfume: Perfume; onPress: () => void }> = ({ 
  perfume, 
  onPress 
}) => (
  <TouchableOpacity style={styles.item} onPress={onPress}>
    <View style={styles.itemIcon}>
      <Ionicons name="water-outline" size={24} color={theme.colors.primary} />
    </View>
    <View style={styles.itemContent}>
      <Text style={styles.itemBrand}>{perfume.brand.toUpperCase()}</Text>
      <Text style={styles.itemName} numberOfLines={1}>{perfume.name}</Text>
      <View style={styles.itemPrices}>
        <Text style={styles.itemThreshold}>
          Deal target: {formatPrice(perfume.good_deal_threshold_gbp)}
        </Text>
        <Text style={styles.itemRetail}>
          Retail: {formatPrice(perfume.typical_retail_gbp)}
        </Text>
      </View>
    </View>
    <Ionicons name="chevron-forward" size={20} color={theme.colors.textMuted} />
  </TouchableOpacity>
);

export const PerfumesScreen: React.FC = () => {
  const navigation = useNavigation<StackNavigationProp<RootStackParamList>>();
  const [searchQuery, setSearchQuery] = useState('');
  
  const { data: perfumes, isLoading, isError, refetch } = useGetPerfumesQuery({
    limit: 100,
    search: searchQuery || undefined,
  });

  const handlePerfumePress = (perfume: Perfume) => {
    navigation.navigate('PerfumeDetails', { perfumeId: perfume.id });
  };

  const renderPerfume: ListRenderItem<Perfume> = useCallback(({ item }) => (
    <PerfumeItem
      perfume={item}
      onPress={() => handlePerfumePress(item)}
    />
  ), []);

  const renderSkeleton = () => (
    <View style={styles.skeletonContainer}>
      {Array.from({ length: 8 }).map((_, index) => (
        <View key={index} style={styles.skeletonItem}>
          <Skeleton width={48} height={48} borderRadius={24} />
          <View style={styles.skeletonText}>
            <Skeleton width="60%" height={14} />
            <Skeleton width="40%" height={12} style={{ marginTop: 8 }} />
          </View>
        </View>
      ))}
    </View>
  );

  if (isLoading && !perfumes) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="light" />
        <View style={styles.header}>
          <Text style={styles.title}>Browse Perfumes</Text>
          <View style={styles.searchContainer}>
            <Ionicons name="search" size={20} color={theme.colors.textMuted} />
            <TextInput
              style={styles.searchInput}
              placeholder="Search perfumes..."
              placeholderTextColor={theme.colors.textMuted}
              value={searchQuery}
              onChangeText={setSearchQuery}
            />
          </View>
        </View>
        {renderSkeleton()}
      </SafeAreaView>
    );
  }

  if (isError) {
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
      <View style={styles.header}>
        <Text style={styles.title}>Browse Perfumes</Text>
        <View style={styles.searchContainer}>
          <Ionicons name="search" size={20} color={theme.colors.textMuted} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search perfumes..."
            placeholderTextColor={theme.colors.textMuted}
            value={searchQuery}
            onChangeText={setSearchQuery}
            autoCapitalize="none"
            autoCorrect={false}
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={() => setSearchQuery('')}>
              <Ionicons name="close-circle" size={20} color={theme.colors.textMuted} />
            </TouchableOpacity>
          )}
        </View>
      </View>

      {!perfumes || perfumes.length === 0 ? (
        <EmptyState
          icon="search-outline"
          title="No perfumes found"
          message={searchQuery 
            ? `No results for "${searchQuery}". Try a different search.`
            : "No perfumes available at the moment."
          }
          actionLabel={searchQuery ? "Clear Search" : undefined}
          onAction={searchQuery ? () => setSearchQuery('') : undefined}
        />
      ) : (
        <FlatList
          data={perfumes}
          renderItem={renderPerfume}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
          ItemSeparatorComponent={() => <View style={styles.separator} />}
        />
      )}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  header: {
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: theme.colors.text,
    marginBottom: theme.spacing.md,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.md,
    paddingHorizontal: theme.spacing.md,
    height: 48,
    gap: theme.spacing.sm,
  },
  searchInput: {
    flex: 1,
    color: theme.colors.text,
    fontSize: 16,
    height: '100%',
  },
  listContent: {
    paddingVertical: theme.spacing.sm,
    paddingBottom: theme.spacing.xxl,
  },
  item: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.md,
    backgroundColor: theme.colors.surface,
  },
  itemIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: theme.colors.surfaceVariant,
    justifyContent: 'center',
    alignItems: 'center',
  },
  itemContent: {
    flex: 1,
    marginLeft: theme.spacing.md,
  },
  itemBrand: {
    fontSize: 11,
    fontWeight: '600',
    color: theme.colors.primary,
    letterSpacing: 0.5,
  },
  itemName: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.text,
    marginTop: 2,
  },
  itemPrices: {
    flexDirection: 'row',
    marginTop: 4,
    gap: theme.spacing.md,
  },
  itemThreshold: {
    fontSize: 13,
    color: theme.colors.success,
  },
  itemRetail: {
    fontSize: 13,
    color: theme.colors.textMuted,
    textDecorationLine: 'line-through',
  },
  separator: {
    height: 1,
    backgroundColor: theme.colors.border,
    marginLeft: 72,
  },
  skeletonContainer: {
    padding: theme.spacing.md,
  },
  skeletonItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: theme.spacing.md,
  },
  skeletonText: {
    flex: 1,
    marginLeft: theme.spacing.md,
  },
});

export default PerfumesScreen;
