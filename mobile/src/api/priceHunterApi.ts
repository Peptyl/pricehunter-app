// RTK Query API Slice for Olfex
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { API_BASE_URL } from './client';
import type {
  Perfume,
  Deal,
  Alert,
  Retailer,
  DealsResponse,
  PerfumesResponse,
} from '../types';

// Define the API slice
export const olfexApi = createApi({
  reducerPath: 'olfexApi',
  baseQuery: fetchBaseQuery({
    baseUrl: API_BASE_URL,
    prepareHeaders: (headers) => {
      // Add auth token when available
      // const token = getState().auth.token;
      // if (token) headers.set('authorization', `Bearer ${token}`);
      return headers;
    },
  }),
  tagTypes: ['Perfumes', 'Deals', 'Alerts', 'Retailers'],
  endpoints: (builder) => ({
    // Perfumes endpoints
    getPerfumes: builder.query<Perfume[], { page?: number; limit?: number; search?: string }>({
      query: ({ page = 1, limit = 20, search }) => ({
        url: '/perfumes',
        params: { page, limit, search },
      }),
      transformResponse: (response: PerfumesResponse) => response.perfumes,
      providesTags: ['Perfumes'],
    }),

    getPerfumeById: builder.query<Perfume, string>({
      query: (id) => `/perfumes/${id}`,
      providesTags: (result, error, id) => [{ type: 'Perfumes', id }],
    }),

    // Deals endpoints
    getDeals: builder.query<Deal[], { page?: number; limit?: number; minSavings?: number }>({
      query: ({ page = 1, limit = 50, minSavings } = {}) => ({
        url: '/deals',
        params: { page, limit, min_savings: minSavings },
      }),
      transformResponse: (response: DealsResponse) => response.deals,
      providesTags: ['Deals'],
    }),

    getDealById: builder.query<Deal, string>({
      query: (id) => `/deals/${id}`,
      providesTags: (result, error, id) => [{ type: 'Deals', id }],
    }),

    // Alerts endpoints
    getAlerts: builder.query<Alert[], void>({
      query: () => '/alerts',
      providesTags: ['Alerts'],
    }),

    createAlert: builder.mutation<Alert, { perfumeId: string; targetPrice: number }>({
      query: (body) => ({
        url: '/alerts',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['Alerts'],
    }),

    deleteAlert: builder.mutation<void, string>({
      query: (id) => ({
        url: `/alerts/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Alerts'],
    }),

    // Retailers endpoints
    getRetailers: builder.query<Retailer[], void>({
      query: () => '/retailers',
      providesTags: ['Retailers'],
    }),
  }),
});

// Export hooks for usage in components
export const {
  useGetPerfumesQuery,
  useGetPerfumeByIdQuery,
  useGetDealsQuery,
  useGetDealByIdQuery,
  useGetAlertsQuery,
  useCreateAlertMutation,
  useDeleteAlertMutation,
  useGetRetailersQuery,
  useLazyGetDealsQuery,
  useLazyGetPerfumesQuery,
} = olfexApi;
