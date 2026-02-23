// Types for PriceHunter Mobile App

export interface Perfume {
  id: string;
  name: string;
  brand: string;
  house?: string;
  description?: string;
  typical_retail_gbp: number;
  good_deal_threshold_gbp: number;
  size_ml?: number;
  concentration?: string;
  notes?: string[];
  image_url?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Deal {
  id: string;
  perfume_id: string;
  perfume: string;
  brand: string;
  retailer: string;
  retailer_url?: string;
  best_price: number;
  retail_price: number;
  savings: number;
  savings_percent: number;
  size_ml?: number;
  in_stock: boolean;
  discovered_at: string;
  expires_at?: string;
  image_url?: string;
}

export interface Alert {
  id: string;
  user_id: string;
  perfume_id: string;
  perfume_name: string;
  target_price: number;
  current_price?: number;
  is_active: boolean;
  created_at: string;
  triggered_at?: string;
}

export interface Retailer {
  id: string;
  name: string;
  base_url: string;
  logo_url?: string;
  rating?: number;
  shipping_info?: string;
}

export interface PriceHistory {
  id: string;
  perfume_id: string;
  retailer_id: string;
  price: number;
  currency: string;
  recorded_at: string;
  in_stock: boolean;
}

export interface ApiResponse<T> {
  data: T;
  status: 'success' | 'error';
  message?: string;
}

export interface DealsResponse {
  deals: Deal[];
  total: number;
  page: number;
  per_page: number;
}

export interface PerfumesResponse {
  perfumes: Perfume[];
  total: number;
  page: number;
  per_page: number;
}

export interface UserPreferences {
  darkMode: boolean;
  notificationsEnabled: boolean;
  preferredBrands: string[];
  priceAlertThreshold: number;
}

// Navigation types
export type RootStackParamList = {
  Main: undefined;
  DealDetails: { dealId: string };
  PerfumeDetails: { perfumeId: string };
  Settings: undefined;
};

export type MainTabParamList = {
  Deals: undefined;
  Perfumes: undefined;
  Alerts: undefined;
  Profile: undefined;
};

// Auth Navigation types
export type AuthStackParamList = {
  SignIn: undefined;
  SignUp: undefined;
};

// Extended root stack with auth
export type AppStackParamList = {
  Auth: undefined;
  Main: undefined;
  DealDetails: { dealId: string };
  PerfumeDetails: { perfumeId: string };
  Settings: undefined;
};
