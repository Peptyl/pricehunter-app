// Deals Slice - Local state management for deals
import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { Deal } from '../types';

interface DealsState {
  selectedDeal: Deal | null;
  filters: {
    minSavings: number;
    maxPrice: number | null;
    brands: string[];
    retailers: string[];
  };
  refreshTimestamp: number;
}

const initialState: DealsState = {
  selectedDeal: null,
  filters: {
    minSavings: 0,
    maxPrice: null,
    brands: [],
    retailers: [],
  },
  refreshTimestamp: Date.now(),
};

const dealsSlice = createSlice({
  name: 'deals',
  initialState,
  reducers: {
    setSelectedDeal: (state, action: PayloadAction<Deal | null>) => {
      state.selectedDeal = action.payload;
    },
    setMinSavingsFilter: (state, action: PayloadAction<number>) => {
      state.filters.minSavings = action.payload;
    },
    setMaxPriceFilter: (state, action: PayloadAction<number | null>) => {
      state.filters.maxPrice = action.payload;
    },
    toggleBrandFilter: (state, action: PayloadAction<string>) => {
      const brand = action.payload;
      if (state.filters.brands.includes(brand)) {
        state.filters.brands = state.filters.brands.filter((b) => b !== brand);
      } else {
        state.filters.brands.push(brand);
      }
    },
    toggleRetailerFilter: (state, action: PayloadAction<string>) => {
      const retailer = action.payload;
      if (state.filters.retailers.includes(retailer)) {
        state.filters.retailers = state.filters.retailers.filter((r) => r !== retailer);
      } else {
        state.filters.retailers.push(retailer);
      }
    },
    clearFilters: (state) => {
      state.filters = {
        minSavings: 0,
        maxPrice: null,
        brands: [],
        retailers: [],
      };
    },
    triggerRefresh: (state) => {
      state.refreshTimestamp = Date.now();
    },
  },
});

export const {
  setSelectedDeal,
  setMinSavingsFilter,
  setMaxPriceFilter,
  toggleBrandFilter,
  toggleRetailerFilter,
  clearFilters,
  triggerRefresh,
} = dealsSlice.actions;

export default dealsSlice.reducer;
