import React, { useState } from 'react';
import { Link as RouterLink, useLocation, useNavigate } from 'react-router-dom';
import {
    AppBar, Toolbar, Typography, Button, IconButton, Box,
    Drawer, List, ListItem, ListItemIcon, ListItemText, Divider, useTheme, useMediaQuery, Theme,
    ListItemButton // Ensure ListItemButton is imported
} from '@mui/material';
// Revert to individual icon imports as the root import didn't solve type issues and might cause others
import MenuIcon from '@mui/icons-material/Menu';
import DashboardIcon from '@mui/icons-material/Dashboard';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import ChatIcon from '@mui/icons-material/Chat';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import SettingsIcon from '@mui/icons-material/Settings';
import LoginIcon from '@mui/icons-material/Login';
import LogoutIcon from '@mui/icons-material/Logout';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';

import { useAuth } from '../../hooks/useAuth'; // Import useAuth

const drawerWidth = 240;

const navItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
    { text: 'Market', icon: <ShowChartIcon />, path: '/market' },
    { text: 'Chat', icon: <ChatIcon />, path: '/chat' }, // New Chat link
    { text: 'Portfolio', icon: <AccountBalanceWalletIcon />, path: '/portfolio' }, // New Portfolio link
    // { text: 'Screener', icon: <SearchIcon />, path: '/screener' }, // Example for future
];

const Navbar = () => { // Removed React.FC
    const theme = useTheme();
    const location = useLocation();
    const isMobile = useMediaQuery(theme.breakpoints.down('md'));
    const [mobileOpen, setMobileOpen] = useState(false);
    const navigate = useNavigate(); // For navigation after logout

    const { isAuthenticated, logout } = useAuth(); // Use actual auth state and logout function

    const handleDrawerToggle = () => {
        setMobileOpen(!mobileOpen);
    };

    const handleLogout = () => {
        logout();
        navigate('/login'); // Redirect to login page after logout
    };

    const drawer = (
        <Box onClick={handleDrawerToggle} sx={{ textAlign: 'center' }}>
            <Typography variant="h6" sx={{ my: 2 }}>
                NAETRA
            </Typography>
            <Divider />
            <List>
                {navItems.map((item) => (
                    <ListItem key={item.text} disablePadding>
                        <ListItemButton 
                            component={RouterLink} 
                            to={item.path}
                            selected={location.pathname === item.path}
                        >
                            <ListItemIcon>{item.icon}</ListItemIcon>
                            <ListItemText primary={item.text} />
                        </ListItemButton>
                    </ListItem>
                ))}
            </List>
            <Divider />
            <List>
                <ListItem disablePadding>
                    <ListItemButton 
                        component={RouterLink} 
                        to="/settings" 
                        selected={location.pathname === '/settings'}
                    >
                        <ListItemIcon><SettingsIcon /></ListItemIcon>
                        <ListItemText primary="Settings" />
                    </ListItemButton>
                </ListItem>
                {isAuthenticated ? (
                     <ListItem disablePadding>
                        <ListItemButton onClick={handleLogout}>
                            <ListItemIcon><LogoutIcon /></ListItemIcon>
                            <ListItemText primary="Logout" />
                        </ListItemButton>
                    </ListItem>
                ) : (
                    <ListItem disablePadding>
                        <ListItemButton component={RouterLink} to="/login"> {/* TODO: Implement login */}
                            <ListItemIcon><LoginIcon /></ListItemIcon>
                            <ListItemText primary="Login" />
                        </ListItemButton>
                    </ListItem>
                )}
            </List>
        </Box>
    );

    return (
        <>
            <AppBar position="fixed" sx={{ zIndex: (theme: Theme) => theme.zIndex.drawer + 1 }}>
                <Toolbar>
                    {isMobile && (
                        <IconButton
                            color="inherit"
                            aria-label="open drawer"
                            edge="start"
                            onClick={handleDrawerToggle}
                            sx={{ mr: 2 }}
                        >
                            <MenuIcon />
                        </IconButton>
                    )}
                    <Typography
                        variant="h6"
                        component={RouterLink}
                        to="/"
                        sx={{ flexGrow: 1, textDecoration: 'none', color: 'inherit', display: { xs: 'none', sm: 'block' } }}
                    >
                        NAETRA
                    </Typography>
                    {!isMobile && (
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            {navItems.map((item) => (
                                <Button
                                    key={item.text}
                                    color="inherit"
                                    component={RouterLink}
                                    to={item.path}
                                    startIcon={item.icon}
                                    sx={{ 
                                        fontWeight: location.pathname === item.path ? 'bold' : 'normal',
                                        borderBottom: location.pathname === item.path ? `2px solid ${theme.palette.common.white}` : 'none',
                                        borderRadius: 0,
                                        mx: 0.5,
                                    }}
                                >
                                    {item.text}
                                </Button>
                            ))}
                            <Divider orientation="vertical" flexItem sx={{ mx: 1, my: 1, borderColor: 'rgba(255,255,255,0.3)' }} />
                            <Button 
                                color="inherit" 
                                component={RouterLink} 
                                to="/settings" 
                                startIcon={<SettingsIcon />}
                                sx={{ fontWeight: location.pathname === '/settings' ? 'bold' : 'normal' }}
                            >
                                Settings
                            </Button>
                            {isAuthenticated ? (
                                <>
                                <IconButton color="inherit" component={RouterLink} to="/profile"> {/* TODO: Create /profile page */}
                                    <AccountCircleIcon />
                                </IconButton>
                                <Button color="inherit" onClick={handleLogout} startIcon={<LogoutIcon />}>
                                    Logout
                                </Button>
                                </>
                            ) : (
                                <Button color="inherit" component={RouterLink} to="/login" startIcon={<LoginIcon />}>
                                    Login
                                </Button>
                            )}
                        </Box>
                    )}
                     {isMobile && ( // Show only title on mobile, drawer has links
                        <Typography variant="h6" component="div" sx={{ flexGrow: 1, textAlign: 'center' }}>
                            NAETRA
                        </Typography>
                    )}
                </Toolbar>
            </AppBar>
            <Box component="nav">
                <Drawer
                    variant={isMobile ? "temporary" : "permanent"}
                    open={isMobile ? mobileOpen : true}
                    onClose={isMobile ? handleDrawerToggle : undefined}
                    ModalProps={{
                        keepMounted: true, // Better open performance on mobile.
                    }}
                    sx={{
                        display: { xs: 'block', md: 'none' }, // Drawer for mobile
                        '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
                    }}
                >
                    {drawer}
                </Drawer>
                 {/* Permanent drawer for larger screens - this part might be better in Layout.tsx if a sidebar is desired */}
                 {/* For now, keeping Navbar simpler and assuming Layout handles main content positioning */}
            </Box>
        </>
    );
};

export default Navbar;
