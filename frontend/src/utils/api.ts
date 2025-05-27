import axios from 'axios';
import { config } from '../config';

export const apiClient = axios.create({
  baseURL: config.apiBaseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Message role enum
export enum MessageRole {
  USER = 'user',
  ASSISTANT = 'assistant',
  SYSTEM = 'system'
}

// API types
export interface ChatMessageResponseData {
  role: MessageRole;
  content: string;
  timestamp: string;
  session_id?: number;
  assistant_response_details?: {
    naetra_thought_process?: string[];
    chart_data?: any;
  };
}

export enum ProcessingEventType {
  INFO = 'info',
  ERROR = 'error',
  PROCESSING = 'processing',
  INTENT = 'intent',
  ANALYSIS = 'analysis',
  THOUGHT = 'thought',
  LEARNING = 'learning',
  DATA_FETCH = 'data_fetch',
  FINAL = 'final',
  PING = 'ping',
  PONG = 'pong',
  CLOSE = 'close',
  STREAM_CHUNK = 'stream_chunk',
  STREAM_END = 'stream_end',
  PROCESSING_UPDATE = 'processing_update'
}

export interface MarketIndices {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
}

export interface StreamEvent {
  event: ProcessingEventType;
  data: string | object;
  timestamp: string;
  metadata?: any;
}

export interface StockSummary {
  symbol: string;
  name: string;
  changePercent: number;
}

export interface SectorPerformance {
  name: string;
  performance: number;
}

export interface MarketOverviewData {
  indices: MarketIndices[];
  gainers: StockSummary[];
  losers: StockSummary[];
  sectors: SectorPerformance[];
}

export interface Portfolio {
  id: number;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user?: {
    id: number;
    username: string;
    email?: string;
  };
}

// API functions
const auth = {
  login: async (credentials: { username: string; password: string }) => {
    try {
      const response = await apiClient.post('/api/v1/auth/login', {
        username: credentials.username,
        password: credentials.password,
        grant_type: 'password'
      });
      
      const authResponse: AuthResponse = response.data;
      console.log('Auth response:', authResponse); // Debug log
      
      if (!authResponse || !authResponse.access_token) {
        console.error('Invalid response:', authResponse);
        throw new Error('Invalid response format from server');
      }

      return {
        token: authResponse.access_token,
        user: authResponse.user || null
      };
    } catch (error: any) {
      console.error('Auth error details:', error.response?.data); // Debug log
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error(error.message || 'Failed to login');
    }
  },
};

const market = {
  getMarketOverview: async (): Promise<MarketOverviewData> => {
    const response = await apiClient.get('/api/v1/market/overview');
    return response.data;
  },
  getSectorPerformance: async (): Promise<SectorPerformance[]> => {
    const response = await apiClient.get('/api/v1/market/sectors');
    return response.data;
  },
};

const portfolio = {
  getPortfolios: async () => {
    const response = await apiClient.get('/api/v1/portfolios');
    return response.data;
  },
  getPortfolioById: async (id: number) => {
    const response = await apiClient.get(`/api/v1/portfolios/${id}`);
    return response.data;
  },
  createPortfolio: async (data: { name: string; description?: string }) => {
    const response = await apiClient.post('/api/v1/portfolios', data);
    return response.data;
  },
  updatePortfolio: async (id: number, data: { name?: string; description?: string }) => {
    const response = await apiClient.patch(`/api/v1/portfolios/${id}`, data);
    return response.data;
  },
  deletePortfolio: async (id: number) => {
    await apiClient.delete(`/api/v1/portfolios/${id}`);
  },
};

const chat = {
  sendMessage: async (content: string, sessionId?: number) => {
    const response = await apiClient.post('/api/v1/chat/message', {
      content,
      session_id: sessionId,
    });
    return response.data;
  },
  getChatHistory: async (sessionId?: number) => {
    const response = await apiClient.get(`/api/v1/chat/history${sessionId ? `?session_id=${sessionId}` : ''}`);
    return response.data;
  },
};

// Main API object
export const api = {
  auth,
  market,
  portfolio,
  chat,
};

// Also export individual functions for direct use
export const {
  getMarketOverview,
  getSectorPerformance,
} = market;

export const {
  getPortfolios,
  getPortfolioById,
} = portfolio;
