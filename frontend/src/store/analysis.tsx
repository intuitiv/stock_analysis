import React from 'react';
import { create } from 'zustand';
// import { getTechnicalAnalysis, getFundamentalAnalysis, ... } from '../utils/api'; // Example API calls

// Define more specific types for analysis results later
type AnalysisResult = any; 
type LoadingState = { [key in AnalysisType]?: boolean };
type AnalysisType = 'technical' | 'fundamental' | 'sentiment' | 'ai' | 'suggestion';

interface AnalysisState {
  currentSymbol: string | null;
  technicalAnalysis: AnalysisResult | null;
  fundamentalAnalysis: AnalysisResult | null;
  sentimentAnalysis: AnalysisResult | null;
  aiInsight: AnalysisResult | null;
  tradingSuggestion: AnalysisResult | null;
  loading: LoadingState;
  error: string | null;
  
  fetchAnalysis: (symbol: string, type: AnalysisType) => Promise<void>;
  setCurrentSymbol: (symbol: string | null) => void;
  clearAnalysis: (type?: AnalysisType) => void;
}

export const useAnalysisStore = create<AnalysisState>((set, get) => ({
  currentSymbol: null,
  technicalAnalysis: null,
  fundamentalAnalysis: null,
  sentimentAnalysis: null,
  aiInsight: null,
  tradingSuggestion: null,
  loading: {},
  error: null,

  setCurrentSymbol: (symbol) => set({ 
      currentSymbol: symbol, 
      // Reset analysis data when symbol changes
      technicalAnalysis: null, 
      fundamentalAnalysis: null, 
      sentimentAnalysis: null, 
      aiInsight: null, 
      tradingSuggestion: null,
      error: null,
      loading: {} 
  }),

  clearAnalysis: (type) => {
      if (type) {
          set({ [type + 'Analysis']: null, error: null, loading: { ...get().loading, [type]: false } });
      } else {
          // Clear all analysis
          set({ 
              technicalAnalysis: null, 
              fundamentalAnalysis: null, 
              sentimentAnalysis: null, 
              aiInsight: null, 
              tradingSuggestion: null,
              error: null,
              loading: {} 
          });
      }
  },

  fetchAnalysis: async (symbol, type) => {
    if (!symbol) return;
    set(state => ({ loading: { ...state.loading, [type]: true }, error: null }));
    
    try {
      let result: AnalysisResult | null = null;
      console.log(`Fetching ${type} analysis for ${symbol}...`);
      // --- TODO: Implement actual API calls based on type ---
      await new Promise(resolve => setTimeout(resolve, 1200)); // Simulate API call
      
      // Dummy data based on type
      if (type === 'technical') {
        result = { rsi: 65.5, macd: 0.5, sma_50: 145.0 };
      } else if (type === 'fundamental') {
        result = { overview: { market_cap: 2e12, pe_ratio: 25.0 }, financials: { total_revenue: 383e9 } };
      } else if (type === 'sentiment') {
         result = { news: { average_score: 0.6, label: "positive" }, overall_score: 0.6 };
      } else if (type === 'ai') {
         result = { prediction: "Slightly Bullish", confidence: 0.7, reasoning: "Dummy AI insight." };
      } else if (type === 'suggestion') {
         result = { suggestion_type: "HOLD", confidence: 0.65, reasoning: "Mixed signals." };
      }
      // --- End of TODO section ---

      // Update state based on type
      const stateUpdate: Partial<AnalysisState> = {};
      switch(type) {
          case 'technical': stateUpdate.technicalAnalysis = result; break;
          case 'fundamental': stateUpdate.fundamentalAnalysis = result; break;
          case 'sentiment': stateUpdate.sentimentAnalysis = result; break;
          case 'ai': stateUpdate.aiInsight = result; break;
          case 'suggestion': stateUpdate.tradingSuggestion = result; break;
      }
      set(state => ({ ...stateUpdate, loading: { ...state.loading, [type]: false } }));

    } catch (err) {
      console.error(`Failed to fetch ${type} analysis for ${symbol}:`, err);
      set(state => ({ error: `Failed to load ${type} analysis`, loading: { ...state.loading, [type]: false } }));
    }
  },
}));