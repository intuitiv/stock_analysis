import React, { ReactNode } from 'react';
import Box from '@mui/material/Box';
// Toolbar import was for an old way of offsetting, not strictly needed for the current marginTop approach.
// import Toolbar from '@mui/material/Toolbar'; 
import Navbar from './Navbar'; 
import { useTheme, Theme } from '@mui/material/styles'; // Import Theme for explicit typing

interface LayoutProps {
  children: ReactNode;
}

const Layout = ({ children }: LayoutProps) => { // Removed JSX.Element return type
  const theme = useTheme<Theme>(); // Explicitly type theme

  // Helper to safely access toolbar minHeight
  const getToolbarMinHeight = (breakpoint?: keyof Theme['breakpoints']['values']): string | number => {
    let minHeightValue: string | number = theme.spacing(8); // Default fallback (64px), removed | undefined
    
    if (theme.mixins?.toolbar) {
        if (breakpoint && theme.mixins.toolbar[breakpoint] && typeof theme.mixins.toolbar[breakpoint] === 'object') {
            const bpToolbar = theme.mixins.toolbar[breakpoint] as any; // Cast to any to access minHeight
            minHeightValue = bpToolbar.minHeight || minHeightValue;
        } else if (typeof theme.mixins.toolbar.minHeight === 'number' || typeof theme.mixins.toolbar.minHeight === 'string') {
            minHeightValue = theme.mixins.toolbar.minHeight || minHeightValue;
        }
    }
    return minHeightValue;
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Navbar /> {/* Assuming Navbar issues will be resolved by environment fix */}
      {/* Main content area */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3, 
          marginTop: getToolbarMinHeight(), // Use helper for safe access
          [theme.breakpoints.up('sm')]: {
            marginTop: getToolbarMinHeight('sm'), // Use helper for sm breakpoint
          },
          width: '100%', 
        }}
      >
        {children}
      </Box>
      {/* Optional Footer can be added here */}
      {/* <Box component="footer" sx={{ p: 2, mt: 'auto', backgroundColor: theme.palette.background.paper }}>
        <Typography variant="body2" color="text.secondary" align="center">
          © {new Date().getFullYear()} NAETRA
        </Typography>
      </Box> */}
    </Box>
  );
};

export default Layout;
