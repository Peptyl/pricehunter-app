// Alerts Screen - User's price alerts
import React from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

import type { Alert } from '../types';
import { useGetAlertsQuery, useDeleteAlertMutation } from '../api/priceHunterApi';
import { theme } from '../theme';
import { formatPrice, formatRelativeTime } from '../utils';

import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';

const AlertItem: React.FC<{
  alert: Alert;
  onDelete: (id: string) => void;
}> = ({ alert, onDelete }) => (
  <View style={styles.item}>
    <View style={styles.itemIcon}>
      <Ionicons 
        name={alert.triggered_at ? "notifications" : "notifications-outline"} 
        size={24} 
        color={alert.triggered_at ? theme.colors.success : theme.colors.primary} 
      />
    </View>
    <View style={styles.itemContent}>
      <Text style={styles.itemName} numberOfLines={1}>
        {alert.perfume_name}
      </Text>
      <Text style={styles.itemTarget}>
        Target: {formatPrice(alert.target_price)}
      </Text>
      <Text style={styles.itemCreated}>
        Created {formatRelativeTime(alert.created_at)}
      </Text>
    </View>
    <TouchableOpacity 
      style={styles.deleteButton}
      onPress={() => onDelete(alert.id)}
    >
      <Ionicons name="trash-outline" size={20} color={theme.colors.error} />
    </TouchableOpacity>
  </View>
);

export const AlertsScreen: React.FC = () => {
  const { data: alerts, isLoading, isError, refetch } = useGetAlertsQuery();
  const [deleteAlert] = useDeleteAlertMutation();

  const handleDelete = async (id: string) => {
    try {
      await deleteAlert(id).unwrap();
    } catch (error) {
      console.error('Failed to delete alert:', error);
    }
  };

  if (isLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="light" />
        <View style={styles.header}>
          <Text style={styles.title}>My Alerts</Text>
        </View>
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading alerts...</Text>
        </View>
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

  if (!alerts || alerts.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="light" />
        <View style={styles.header}>
          <Text style={styles.title}>My Alerts</Text>
        </View>
        <EmptyState
          icon="notifications-outline"
          title="No Alerts Yet"
          message="Set price alerts for your favorite perfumes and we'll notify you when the price drops!"
          actionLabel="Browse Perfumes"
          onAction={() => {}}
        />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" />
      <View style={styles.header}>
        <Text style={styles.title}>My Alerts</Text>
        <Text style={styles.subtitle}>
          {alerts.length} active alert{alerts.length !== 1 ? 's' : ''}
        </Text>
      </View>

      <FlatList
        data={alerts}
        renderItem={({ item }) => (
          <AlertItem alert={item} onDelete={handleDelete} />
        )}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        ItemSeparatorComponent={() => <View style={styles.separator} />}
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: theme.colors.textSecondary,
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
  itemName: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.text,
  },
  itemTarget: {
    fontSize: 14,
    color: theme.colors.success,
    marginTop: 4,
  },
  itemCreated: {
    fontSize: 12,
    color: theme.colors.textMuted,
    marginTop: 2,
  },
  deleteButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  separator: {
    height: 1,
    backgroundColor: theme.colors.border,
    marginLeft: 72,
  },
});

export default AlertsScreen;
