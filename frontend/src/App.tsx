import React from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate, Outlet } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

// Auth
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LoginPage from './pages/LoginPage';

// Import components and pages
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import StockAnalysis from './pages/StockAnalysis';
import MarketOverview from './pages/MarketOverview';
import Settings from './pages/Settings';
import ChatPage from './pages/ChatPage';

// Create theme
const theme = createTheme({
  palette: {
    mode: 'dark', // Use dark mode
    primary: {
      main: '#90caf9', // Light blue for primary elements
    },
    secondary: {
      main: '#f48fb1', // Pink for secondary elements
    },
    background: {
      default: '#121212', // Dark background
      paper: '#1e1e1e', // Slightly lighter paper background
    },
    text: {
      primary: '#ffffff', // White text
      secondary: '#b0bec5', // Grey text
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: { fontSize: '2.5rem', fontWeight: 500 },
    h2: { fontSize: '2rem', fontWeight: 500 },
    h3: { fontSize: '1.75rem', fontWeight: 500 },
    h4: { fontSize: '1.5rem', fontWeight: 500 },
    h5: { fontSize: '1.25rem', fontWeight: 500 },
    h6: { fontSize: '1rem', fontWeight: 500 },
  },
  components: {
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#1e1e1e', // Match paper background
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: '#1e1e1e',
        },
      },
    },
  },
});

// Protected Route Component
const ProtectedRoute: React.FC = () => {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  // Render child routes within the Layout
  return (
    <Layout>
      <Outlet /> 
    </Layout>
  );
};


function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route element={<ProtectedRoute />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/dashboard" element={<Dashboard />} /> {/* Explicit dashboard route */}
              <Route path="/analysis/:symbol" element={<StockAnalysis />} />
              <Route path="/market" element={<MarketOverview />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/chat" element={<ChatPage />} />
            </Route>
            {/* Add other public routes or redirect for unmatched routes if needed */}
            <Route path="*" element={<Navigate to="/" replace />} /> {/* Redirect unmatched to dashboard or login */}
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
