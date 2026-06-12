import React from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Box, Drawer, List, ListItem, ListItemIcon, ListItemText,
  AppBar, Toolbar, Typography, IconButton, Avatar
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Person as AgentIcon,
  Psychology as ModelIcon,
  Logout as LogoutIcon,
} from '@mui/icons-material';
import { useAuth } from '../../context/AuthContext';

const drawerWidth = 240;

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
  { text: 'Agent View', icon: <AgentIcon />, path: '/agent-view' },
  { text: 'Model Insights', icon: <ModelIcon />, path: '/model-insights' },
];

const Layout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <Box sx={{ display: 'flex' }}>
      {/* App Bar */}
      <AppBar 
        position="fixed" 
        sx={{ 
          zIndex: 1201,
          bgcolor: '#1a1f2e',
          borderBottom: '1px solid #00e5ff22'
        }}
      >
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1, color: '#00e5ff' }}>
            ⚡ NBA Cross-Sell Engine
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2" sx={{ color: '#888' }}>
              {user?.name}
            </Typography>
            <Avatar sx={{ bgcolor: '#00e5ff', width: 32, height: 32, fontSize: 14 }}>
              {user?.name?.[0] || 'A'}
            </Avatar>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Sidebar */}
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            bgcolor: '#1a1f2e',
            borderRight: '1px solid #00e5ff22',
          },
        }}
      >
        <Toolbar />
        <List sx={{ mt: 2 }}>
          {menuItems.map((item) => (
            <ListItem
              button
              key={item.text}
              onClick={() => navigate(item.path)}
              sx={{
                mx: 1,
                borderRadius: 1,
                mb: 0.5,
                bgcolor: location.pathname === item.path ? '#00e5ff22' : 'transparent',
                '&:hover': { bgcolor: '#00e5ff11' },
              }}
            >
              <ListItemIcon sx={{ color: location.pathname === item.path ? '#00e5ff' : '#888' }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText 
                primary={item.text} 
                sx={{ 
                  color: location.pathname === item.path ? '#00e5ff' : '#888',
                  '& .MuiTypography-root': { fontSize: 14 }
                }} 
              />
            </ListItem>
          ))}
        </List>
        <Box sx={{ flexGrow: 1 }} />
        <List>
          <ListItem 
            button 
            onClick={handleLogout}
            sx={{ mx: 1, borderRadius: 1, '&:hover': { bgcolor: '#ff408122' } }}
          >
            <ListItemIcon sx={{ color: '#ff4081' }}>
              <LogoutIcon />
            </ListItemIcon>
            <ListItemText primary="Logout" sx={{ color: '#ff4081' }} />
          </ListItem>
        </List>
      </Drawer>

      {/* Main Content */}
      <Box 
        component="main" 
        sx={{ 
          flexGrow: 1, 
          p: 3,
          mt: 8,
          ml: `${drawerWidth}px`,
          minHeight: '100vh',
          bgcolor: '#0b0f19'
        }}
      >
        <Outlet />
      </Box>
    </Box>
  );
};

export default Layout;