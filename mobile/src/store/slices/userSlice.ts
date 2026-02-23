// User Slice - User preferences and settings
import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { UserPreferences } from '../types';

interface UserState {
  preferences: UserPreferences;
  isAuthenticated: boolean;
  userId: string | null;
  email: string | null;
}

const initialState: UserState = {
  preferences: {
    darkMode: true,
    notificationsEnabled: true,
    preferredBrands: [],
    priceAlertThreshold: 10, // 10% savings threshold
  },
  isAuthenticated: false,
  userId: null,
  email: null,
};

const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    setDarkMode: (state, action: PayloadAction<boolean>) => {
      state.preferences.darkMode = action.payload;
    },
    setNotificationsEnabled: (state, action: PayloadAction<boolean>) => {
      state.preferences.notificationsEnabled = action.payload;
    },
    setPriceAlertThreshold: (state, action: PayloadAction<number>) => {
      state.preferences.priceAlertThreshold = action.payload;
    },
    addPreferredBrand: (state, action: PayloadAction<string>) => {
      if (!state.preferences.preferredBrands.includes(action.payload)) {
        state.preferences.preferredBrands.push(action.payload);
      }
    },
    removePreferredBrand: (state, action: PayloadAction<string>) => {
      state.preferences.preferredBrands = state.preferences.preferredBrands.filter(
        (brand) => brand !== action.payload
      );
    },
    setUser: (state, action: PayloadAction<{ userId: string; email: string }>) => {
      state.isAuthenticated = true;
      state.userId = action.payload.userId;
      state.email = action.payload.email;
    },
    logout: (state) => {
      state.isAuthenticated = false;
      state.userId = null;
      state.email = null;
    },
    updatePreferences: (state, action: PayloadAction<Partial<UserPreferences>>) => {
      state.preferences = { ...state.preferences, ...action.payload };
    },
  },
});

export const {
  setDarkMode,
  setNotificationsEnabled,
  setPriceAlertThreshold,
  addPreferredBrand,
  removePreferredBrand,
  setUser,
  logout,
  updatePreferences,
} = userSlice.actions;

export default userSlice.reducer;
