export const config = {
  apiBaseUrl: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',
  // Add other configuration values as needed
  defaultPageSize: 10,
  maxChatHistoryLength: 100,
  chartRefreshInterval: 60000, // 1 minute
};
