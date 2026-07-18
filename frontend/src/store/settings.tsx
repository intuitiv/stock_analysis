import React from 'react';
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

type ThemeMode = 'light' | 'dark';

interface SettingsState {
  themeMode: ThemeMode;
  // Add API keys, feature flags, preferences etc. that need to be persisted
  // Example: Store API keys securely if needed, or manage them server-side
  // apiKeyGemini: string | null; 
  featureFlags: { [key: string]: boolean };
  watchlist: string[];
  // Add other user preferences like chart settings, notification preferences etc.

  setThemeMode: (mode: ThemeMode) => void;
  // setApiKey: (service: string, key: string | null) => void;
  toggleFeatureFlag: (feature: string) => void;
  addToWatchlist: (symbol: string) => void;
  removeFromWatchlist: (symbol: string) => void;
  loadServerSettings: () => Promise<void>; // Action to load settings from backend
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set, get) => ({
      themeMode: 'dark', // Default theme
      // apiKeyGemini: null, // Avoid storing sensitive keys in localStorage if possible
      featureFlags: { // Default client-side flags (can be overridden by backend)
          advancedTechnicals: false,
          newsAnalysis: false,
          socialSentiment: false,
          mlPredictions: false,
          patternRecognition: false,
          aiStrategies: false,
          portfolioTracking: true, // Example: enabled by default
          realtimeUpdates: false,
          // Add other flags corresponding to .env.custom ENABLE_* flags
      },
      watchlist: ['AAPL', 'GOOGL', 'MSFT', 'TSLA'], // Default watchlist

      setThemeMode: (mode) => set({ themeMode: mode }),

      // setApiKey: (service, key) => set({ [`apiKey${service}`]: key }), // Example if storing keys needed

      toggleFeatureFlag: (feature) => set((state) => ({
          featureFlags: {
              ...state.featureFlags,
              [feature]: !state.featureFlags[feature]
          }
      })),

      addToWatchlist: (symbol) => set((state) => {
          const upperSymbol = symbol.toUpperCase();
          if (!state.watchlist.includes(upperSymbol)) {
              return { watchlist: [...state.watchlist, upperSymbol] };
          }
          return {}; // No change if already present
      }),

      removeFromWatchlist: (symbol) => set((state) => ({
          watchlist: state.watchlist.filter(s => s !== symbol.toUpperCase())
      })),
      
      loadServerSettings: async () => {
          // TODO: Implement API call to fetch user-specific settings/feature flags from backend
          console.log("Loading server settings (not implemented)...");
          // Example: Fetch settings and update store
          // const serverSettings = await fetch('/api/v1/settings/preferences'); 
          // const data = await serverSettings.json();
          // set({ featureFlags: data.featureFlags, ... other settings ... });
      }
    }),
    {
      name: 'naetra-settings-storage', // Name of the item in storage (localStorage by default)
      storage: createJSONStorage(() => localStorage), // Use localStorage
      // partialize: (state) => ({ themeMode: state.themeMode, watchlist: state.watchlist }), // Only persist specific parts
    }
  )
);

// Optional: Load server settings when the app initializes
// useSettingsStore.getState().loadServerSettings();