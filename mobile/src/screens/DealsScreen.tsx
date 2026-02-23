// Deals Screen - Main feed of active deals
import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  RefreshControl,
  ListRenderItem,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaView } from 'react-native-safe-area-context';

import type { RootStackParamList, Deal } from '../types';
import { useGetDealsQuery, useLazyGetDealsQuery } from '../api/priceHunterApi';
import { theme } from '../theme';

import DealCard from '../components/DealCard';
import { DealCardSkeleton } from '../components/Skeleton';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';

const SKELETON_COUNT = 5;

export const DealsScreen: React.FC = () => {
  const navigation = useNavigation<StackNavigationProp<RootStackParamList>>();
  const [refreshing, setRefreshing] = useState(false);
  
  const { data: deals, isLoading, isError, refetch } = useGetDealsQuery({
    limit: 50,
  });
  
  const [triggerRefetch] = useLazyGetDealsQuery();

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  }, [refetch]);

  const handleDealPress = (deal: Deal) => {
    navigation.navigate('DealDetails', { dealId: deal.id });
  };

  const handleBuyNow = (deal: Deal) => {
    // Open retailer URL or show options
    console.log('Buy now:', deal.retailer_url);
  };

  const renderDeal: ListRenderItem<Deal> = useCallback(({ item }) => (
    <DealCard
      deal={item}
      onPress={handleDealPress}
      onBuyNow={handleBuyNow}
    />
  ), []);

  const renderSkeleton = () => (
    <>
      {Array.from({ length: SKELETON_COUNT }).map((_, index) => (
        <DealCardSkeleton key={index} />
      ))}
    </>
  );

  if (isLoading && !deals) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="light" />
        <View style={styles.header}>
          <Text style={styles.title}>🔥 Today's Deals</Text>
          <Text style={styles.subtitle}>Finding the best niche perfume prices</Text>
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

  if (!deals || deals.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="light" />
        <EmptyState
          icon="flame-outline"
          title="No Active Deals"
          message="We're scanning retailers right now. Check back at 12pm or 6pm for fresh deals!"
          actionLabel="Refresh"
          onAction={refetch}
        />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" />
      <View style={styles.header}>
        <Text style={styles.title}>🔥 Today's Deals</Text>
        <Text style={styles.subtitle}>
          {deals.length} active deals found
        </Text>
      </View>
      
      <FlatList
        data={deals}
        renderItem={renderDeal}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={theme.colors.primary}
            colors={[theme.colors.primary]}
          />
        }
        showsVerticalScrollIndicator={false}
        initialNumToRender={10}
        maxToRenderPerBatch={10}
        windowSize={5}
        removeClippedSubviews={true}
      />
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
  },
  subtitle: {
    fontSize: 14,
    color: theme.colors.textSecondary,
    marginTop: theme.spacing.xs,
  },
  listContent: {
    paddingVertical: theme.spacing.sm,
    paddingBottom: theme.spacing.xxl,
  },
});

export default DealsScreen;
