// RevenueCat Hook - Manage subscriptions and purchases
import { useState, useEffect, useCallback } from 'react';
import Purchases, { 
  CustomerInfo, 
  PurchasesOffering, 
  PurchasesPackage,
  LOG_LEVEL,
} from 'react-native-purchases';
import { Platform } from 'react-native';
import Constants from 'expo-constants';

// RevenueCat API keys - replace with your actual keys from RevenueCat dashboard
const REVENUECAT_API_KEY = Platform.select({
  ios: Constants.expoConfig?.extra?.revenueCatApiKeyIOS || 'appl_YOUR_IOS_KEY',
  android: Constants.expoConfig?.extra?.revenueCatApiKeyAndroid || 'goog_YOUR_ANDROID_KEY',
  default: 'goog_YOUR_ANDROID_KEY',
});

// Entitlement IDs from RevenueCat dashboard
export const ENTITLEMENTS = {
  PRO: 'pro',
  PREMIUM: 'premium',
} as const;

// Offering IDs from RevenueCat dashboard
export const OFFERINGS = {
  PRO: 'pro',
} as const;

export interface SubscriptionState {
  isLoading: boolean;
  customerInfo: CustomerInfo | null;
  offerings: PurchasesOffering | null;
  isPro: boolean;
  error: string | null;
}

export const useRevenueCat = () => {
  const [state, setState] = useState<SubscriptionState>({
    isLoading: true,
    customerInfo: null,
    offerings: null,
    isPro: false,
    error: null,
  });

  // Initialize RevenueCat
  useEffect(() => {
    const initPurchases = async () => {
      try {
        // Configure RevenueCat
        Purchases.setLogLevel(LOG_LEVEL.DEBUG);
        Purchases.configure({ apiKey: REVENUECAT_API_KEY });

        // Get initial customer info
        const customerInfo = await Purchases.getCustomerInfo();
        
        // Get available offerings
        const offerings = await Purchases.getOfferings();

        // Check if user has Pro entitlement
        const isPro = customerInfo.entitlements.active[ENTITLEMENTS.PRO]?.isActive === true;

        setState({
          isLoading: false,
          customerInfo,
          offerings: offerings.current,
          isPro,
          error: null,
        });

        console.log('[RevenueCat] Initialized successfully');
        console.log('[RevenueCat] Customer Info:', JSON.stringify(customerInfo, null, 2));
        console.log('[RevenueCat] Offerings:', JSON.stringify(offerings, null, 2));
      } catch (error: any) {
        console.error('[RevenueCat] Initialization error:', error);
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: error.message || 'Failed to initialize purchases',
        }));
      }
    };

    initPurchases();

    // Set up customer info update listener
    const unsubscribe = Purchases.addCustomerInfoUpdateListener((customerInfo) => {
      const isPro = customerInfo.entitlements.active[ENTITLEMENTS.PRO]?.isActive === true;
      setState(prev => ({
        ...prev,
        customerInfo,
        isPro,
      }));
    });

    return () => {
      unsubscribe();
    };
  }, []);

  // Purchase a package
  const purchasePackage = useCallback(async (pack: PurchasesPackage): Promise<boolean> => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const { customerInfo } = await Purchases.purchasePackage(pack);
      const isPro = customerInfo.entitlements.active[ENTITLEMENTS.PRO]?.isActive === true;
      
      setState(prev => ({
        ...prev,
        customerInfo,
        isPro,
        isLoading: false,
      }));

      console.log('[RevenueCat] Purchase successful:', pack.identifier);
      return true;
    } catch (error: any) {
      // User cancelled - not a real error
      if (error.userCancelled) {
        console.log('[RevenueCat] User cancelled purchase');
        setState(prev => ({ ...prev, isLoading: false }));
        return false;
      }

      console.error('[RevenueCat] Purchase error:', error);
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error.message || 'Purchase failed',
      }));
      return false;
    }
  }, []);

  // Restore purchases
  const restorePurchases = useCallback(async (): Promise<boolean> => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const customerInfo = await Purchases.restorePurchases();
      const isPro = customerInfo.entitlements.active[ENTITLEMENTS.PRO]?.isActive === true;
      
      setState(prev => ({
        ...prev,
        customerInfo,
        isPro,
        isLoading: false,
      }));

      console.log('[RevenueCat] Purchases restored. Pro:', isPro);
      return isPro;
    } catch (error: any) {
      console.error('[RevenueCat] Restore error:', error);
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error.message || 'Failed to restore purchases',
      }));
      return false;
    }
  }, []);

  // Get Pro package (monthly/annual)
  const getProPackage = useCallback((annual: boolean = false): PurchasesPackage | null => {
    if (!state.offerings) return null;
    
    const availablePackages = state.offerings.availablePackages;
    if (!availablePackages || availablePackages.length === 0) return null;

    // Find annual or monthly package
    if (annual) {
      return availablePackages.find(p => p.identifier.includes('annual')) || availablePackages[0];
    }
    return availablePackages.find(p => p.identifier.includes('monthly')) || availablePackages[0];
  }, [state.offerings]);

  // Sync user ID with RevenueCat (for cross-platform/account linking)
  const syncUserId = useCallback(async (userId: string) => {
    try {
      await Purchases.logIn(userId);
      console.log('[RevenueCat] User ID synced:', userId);
    } catch (error) {
      console.error('[RevenueCat] Failed to sync user ID:', error);
    }
  }, []);

  // Logout from RevenueCat
  const logout = useCallback(async () => {
    try {
      await Purchases.logOut();
      console.log('[RevenueCat] User logged out');
    } catch (error) {
      console.error('[RevenueCat] Failed to logout:', error);
    }
  }, []);

  return {
    ...state,
    purchasePackage,
    restorePurchases,
    getProPackage,
    syncUserId,
    logout,
  };
};

export default useRevenueCat;
