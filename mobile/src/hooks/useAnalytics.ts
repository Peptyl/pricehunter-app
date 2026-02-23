// Firebase Analytics Hook - Track app events
import { useCallback, useEffect } from 'react';
import analytics from '@react-native-firebase/analytics';
import { useRoute } from '@react-navigation/native';

export const useAnalytics = () => {
  const route = useRoute();

  // Log a custom event
  const logEvent = useCallback(async (eventName: string, params?: Record<string, any>) => {
    try {
      await analytics().logEvent(eventName, {
        ...params,
        screen_name: route.name,
        timestamp: new Date().toISOString(),
      });
      console.log(`[Analytics] Event: ${eventName}`, params);
    } catch (error) {
      console.error('[Analytics] Failed to log event:', error);
    }
  }, [route.name]);

  // Log screen view
  const logScreenView = useCallback(async (screenName: string, screenClass?: string) => {
    try {
      await analytics().logScreenView({
        screen_name: screenName,
        screen_class: screenClass || screenName,
      });
      console.log(`[Analytics] Screen View: ${screenName}`);
    } catch (error) {
      console.error('[Analytics] Failed to log screen view:', error);
    }
  }, []);

  // Log search event
  const logSearch = useCallback(async (searchTerm: string) => {
    try {
      await analytics().logSearch({ search_term: searchTerm });
      console.log(`[Analytics] Search: ${searchTerm}`);
    } catch (error) {
      console.error('[Analytics] Failed to log search:', error);
    }
  }, []);

  // Log select content (for deal views, perfume views)
  const logSelectContent = useCallback(async (contentType: string, itemId: string, itemName?: string) => {
    try {
      await analytics().logSelectContent({
        content_type: contentType,
        item_id: itemId,
      });
      console.log(`[Analytics] Select Content: ${contentType} - ${itemId}`);
    } catch (error) {
      console.error('[Analytics] Failed to log select content:', error);
    }
  }, []);

  // Log purchase/subscription
  const logPurchase = useCallback(async (params: {
    transactionId: string;
    value: number;
    currency: string;
    itemName: string;
  }) => {
    try {
      await analytics().logPurchase({
        transaction_id: params.transactionId,
        value: params.value,
        currency: params.currency,
        items: [{
          item_name: params.itemName,
          item_category: 'subscription',
        }],
      });
      console.log(`[Analytics] Purchase: ${params.itemName} - ${params.value} ${params.currency}`);
    } catch (error) {
      console.error('[Analytics] Failed to log purchase:', error);
    }
  }, []);

  // Set user properties
  const setUserProperties = useCallback(async (properties: Record<string, string | null>) => {
    try {
      for (const [key, value] of Object.entries(properties)) {
        await analytics().setUserProperty(key, value);
      }
    } catch (error) {
      console.error('[Analytics] Failed to set user properties:', error);
    }
  }, []);

  // Set user ID
  const setUserId = useCallback(async (userId: string | null) => {
    try {
      await analytics().setUserId(userId);
      console.log(`[Analytics] User ID set: ${userId}`);
    } catch (error) {
      console.error('[Analytics] Failed to set user ID:', error);
    }
  }, []);

  return {
    logEvent,
    logScreenView,
    logSearch,
    logSelectContent,
    logPurchase,
    setUserProperties,
    setUserId,
  };
};

// Hook for automatic screen tracking
export const useScreenTracking = (screenName: string) => {
  const { logScreenView } = useAnalytics();

  useEffect(() => {
    logScreenView(screenName);
  }, [screenName, logScreenView]);
};

export default useAnalytics;
