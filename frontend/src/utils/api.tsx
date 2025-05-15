import React from 'react';
import axios, { InternalAxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';

// TODO: Get base URL from environment variables or config
// Assuming backend runs on http://localhost:8000 during development
const API_BASE_URL = 'http://localhost:8000/api/v1'; 

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    // TODO: Add Authorization header if using JWT tokens
    // Example: Retrieve token from localStorage or state management
    // 'Authorization': `Bearer ${localStorage.getItem('authToken')}` 
  },
  timeout: 10000, // Set a reasonable timeout (10 seconds)
});

// Optional: Add interceptors for request/response logging or error handling
// Use InternalAxiosRequestConfig and AxiosResponse for proper typing

apiClient.interceptors.request.use((request: InternalAxiosRequestConfig) => {
  console.log('Starting Request:', request.method?.toUpperCase(), request.url);
  // Example: Add token if available
  // const token = localStorage.getItem('authToken');
  // if (token) {
  //   request.headers.Authorization = `Bearer ${token}`;
  // }
  return request;
});

apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // console.log('Response Status:', response.status);
    // console.log('Response Data:', response.data);
    return response;
  }, 
  (error: AxiosError) => {
    console.error('API Error Status:', error.response?.status);
    console.error('API Error Data:', error.response?.data);
    console.error('API Error Message:', error.message);
    // TODO: Add global error handling (e.g., show notification, redirect to login on 401)
    // Example: if (error.response?.status === 401) { /* redirect to login */ }
    return Promise.reject(error);
});


// --- Market Data ---

export const getMarketOverview = async () => {
  const response = await apiClient.get('/market/overview');
  return response.data; // Axios automatically parses JSON
};

export const searchStocks = async (query: string) => {
  const response = await apiClient.get('/market/search', { params: { query } });
  return response.data;
};

export const getSectorPerformance = async () => {
    const response = await apiClient.get('/market/sectors');
    return response.data;
};

// --- Stock Data ---

export const getStockProfile = async (symbol: string) => {
  const response = await apiClient.get(`/stocks/${symbol}/profile`);
  return response.data;
};

export const getHistoricalData = async (symbol: string, period: string = '1y', interval: string = '1d') => {
  const response = await apiClient.get(`/stocks/${symbol}/historical`, { params: { period, interval } });
  return response.data;
};

export const getRealtimeQuote = async (symbol: string) => {
    const response = await apiClient.get(`/stocks/${symbol}/quote`);
    return response.data;
};

export const getStockNews = async (symbol: string, limit: number = 10) => {
    const response = await apiClient.get(`/stocks/${symbol}/news`, { params: { limit } });
    return response.data;
};

// --- Analysis ---

export const getTechnicalAnalysis = async (symbol: string) => {
    const response = await apiClient.get(`/analysis/${symbol}/technical`);
    return response.data;
};

export const getFundamentalAnalysis = async (symbol: string) => {
    const response = await apiClient.get(`/analysis/${symbol}/fundamental`);
    return response.data;
};

export const getSentimentAnalysis = async (symbol: string) => {
    const response = await apiClient.get(`/analysis/${symbol}/sentiment`);
    return response.data;
};

export const getAiInsight = async (symbol: string, prompt?: string) => {
    const response = await apiClient.post(`/analysis/${symbol}/ai-insight`, null, { params: { prompt } }); // POST might be better if prompt is long
    return response.data;
};

export const getTradingSuggestion = async (symbol: string) => {
    const response = await apiClient.get(`/analysis/${symbol}/suggestion`);
    return response.data;
};

// --- Authentication --- (Example)

// export const login = async (credentials: { username: string, password: string }) => {
//     const formData = new URLSearchParams();
//     formData.append('username', credentials.username);
//     formData.append('password', credentials.password);
//     const response = await apiClient.post('/auth/token', formData, {
//         headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
//     });
//     // TODO: Store the token (e.g., localStorage, state management)
//     // localStorage.setItem('authToken', response.data.access_token);
//     return response.data;
// };

// --- Portfolio ---

export const getPortfolios = async () => {
  const response = await apiClient.get('/portfolios');
  return response.data;
};

export const getPortfolioById = async (portfolioId: string) => {
  const response = await apiClient.get(`/portfolios/${portfolioId}`);
  return response.data;
};

// Example: Add a new portfolio
// export const createPortfolio = async (name: string) => {
//   const response = await apiClient.post('/portfolios', { name });
//   return response.data;
// };

// Example: Add a position to a portfolio
// export const addPositionToPortfolio = async (portfolioId: string, positionData: { symbol: string, quantity: number, purchase_price: number }) => {
//   const response = await apiClient.post(`/portfolios/${portfolioId}/positions`, positionData);
//   return response.data;
// };

// --- Settings --- (Placeholder)

// export const getUserSettings = async () => { ... }
// export const updateUserSettings = async (settingsData: any) => { ... }

// --- Chat ---

// Types based on app/schemas/chat_schemas.py (mirrored in ChatPage.tsx)
enum MessageRole {
  USER = "user",
  ASSISTANT = "assistant",
  SYSTEM = "system",
}

interface ChatContext {
  current_symbol?: string | null;
  current_timeframe?: string | null;
  active_portfolio_id?: number | null;
  user_risk_profile?: string;
}

interface ChatMessageCreatePayload { // For POST /chat/message
  session_id?: number | null;
  content: string;
  context?: ChatContext | null;
}

interface ChatMessageResponseData {
  id: number;
  session_id: number;
  role: MessageRole;
  content: string;
  timestamp: string;
  context_at_message?: ChatContext | null;
  assistant_response_details?: Record<string, any> | null;
}

interface ChatApiResponseData { // Response for POST /chat/message
  session_id: number;
  user_message: ChatMessageResponseData;
  assistant_message: ChatMessageResponseData;
  updated_context: ChatContext;
}

interface ChatSessionResponseData {
  id: number;
  user_id: number;
  title?: string | null;
  context: ChatContext;
  created_at: string;
  updated_at?: string | null;
  messages: ChatMessageResponseData[];
}

export const sendChatMessage = async (payload: ChatMessageCreatePayload): Promise<ChatApiResponseData> => {
  const response = await apiClient.post('/chat/message', payload);
  return response.data;
};

export const listChatSessions = async (skip: number = 0, limit: number = 20): Promise<ChatSessionResponseData[]> => {
  const response = await apiClient.get('/chat/sessions', { params: { skip, limit } });
  return response.data;
};

export const getChatSessionHistory = async (
  sessionId: number, 
  messageLimit: number = 50, 
  messageOffset: number = 0
): Promise<ChatSessionResponseData> => {
  const response = await apiClient.get(`/chat/sessions/${sessionId}`, { 
    params: { message_limit: messageLimit, message_offset: messageOffset } 
  });
  return response.data;
};