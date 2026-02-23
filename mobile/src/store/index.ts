// Redux Store Configuration
import { configureStore } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';
import { priceHunterApi } from '../api/priceHunterApi';
import dealsSlice from './slices/dealsSlice';
import userSlice from './slices/userSlice';

export const store = configureStore({
  reducer: {
    // API slices
    [priceHunterApi.reducerPath]: priceHunterApi.reducer,
    
    // Feature slices
    deals: dealsSlice,
    user: userSlice,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }).concat(priceHunterApi.middleware),
  devTools: process.env.NODE_ENV !== 'production',
});

// Enable refetchOnFocus/refetchOnReconnect behaviors
setupListeners(store.dispatch);

// Export types
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
