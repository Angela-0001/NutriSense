import React, { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  Box, Drawer, AppBar, Toolbar, Typography, List, ListItemButton,
  ListItemIcon, ListItemText, IconButton, Avatar, Tooltip, Divider, useTheme
} from '@mui/material'
import DashboardIcon    from '@mui/icons-material/Dashboard'
import RestaurantIcon   from '@mui/icons-material/Restaurant'
import AnalyticsIcon    from '@mui/icons-material/Analytics'
import BubbleChartIcon  from '@mui/icons-material/BubbleChart'
import FactCheckIcon    from '@mui/icons-material/FactCheck'
import CalendarMonthIcon from '@mui/icons-material/CalendarMonth'
import AutoAwesomeIcon  from '@mui/icons-material/AutoAwesome'
import PersonIcon       from '@mui/icons-material/Person'
import LogoutIcon       from '@mui/icons-material/Logout'
import MenuIcon         from '@mui/icons-material/Menu'
import { useAuth } from '../context/AuthContext'

const DRAWER_WIDTH = 240

const NAV_ITEMS = [
  { label: 'Dashboard',      path: '/',          icon: <DashboardIcon /> },
  { label: 'Food Log',       path: '/log',        icon: <RestaurantIcon /> },
  { label: 'Analysis',       path: '/analysis',   icon: <AnalyticsIcon /> },
  { label: 'Disease Risk',   path: '/bayesian',   icon: <BubbleChartIcon /> },
  { label: 'Claim Validator',path: '/claims',     icon: <FactCheckIcon /> },
  { label: 'Dietary Advice',  path: '/meal-plan',  icon: <CalendarMonthIcon /> },
  { label: 'AI Dataset',     path: '/dataset',    icon: <AutoAwesomeIcon /> },
  { label: 'Profile',        path: '/profile',    icon: <PersonIcon /> },
]

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const theme = useTheme()
  const [mobileOpen, setMobileOpen] = useState(false)

  const drawer = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Toolbar sx={{ gap: 1 }}>
        <Box component="span" sx={{ fontSize: 28 }}>🥗</Box>
        <Typography variant="h6" color="primary" fontWeight={700}>NutriSense</Typography>
      </Toolbar>
      <Divider />
      <List sx={{ flex: 1, pt: 1 }}>
        {NAV_ITEMS.map(item => (
          <ListItemButton
            key={item.path}
            selected={location.pathname === item.path}
            onClick={() => { navigate(item.path); setMobileOpen(false) }}
            sx={{
              mx: 1, borderRadius: 2, mb: 0.5,
              '&.Mui-selected': {
                bgcolor: theme.palette.primary.main + '18',
                color: theme.palette.primary.main,
                '& .MuiListItemIcon-root': { color: theme.palette.primary.main }
              }
            }}
          >
            <ListItemIcon sx={{ minWidth: 40 }}>{item.icon}</ListItemIcon>
            <ListItemText primary={item.label} primaryTypographyProps={{ fontSize: 14, fontWeight: 500 }} />
          </ListItemButton>
        ))}
      </List>
      <Divider />
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
        <Avatar sx={{ width: 32, height: 32, bgcolor: theme.palette.primary.main, fontSize: 14 }}>
          {user?.name?.[0]?.toUpperCase()}
        </Avatar>
        <Box sx={{ flex: 1, overflow: 'hidden' }}>
          <Typography variant="body2" fontWeight={600} noWrap>{user?.name}</Typography>
          <Typography variant="caption" color="text.secondary" noWrap>{user?.email}</Typography>
        </Box>
        <Tooltip title="Logout">
          <IconButton size="small" onClick={logout}><LogoutIcon fontSize="small" /></IconButton>
        </Tooltip>
      </Box>
    </Box>
  )

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* Mobile AppBar */}
      <AppBar position="fixed" sx={{ display: { sm: 'none' }, bgcolor: 'white', color: 'text.primary', boxShadow: 1 }}>
        <Toolbar>
          <IconButton edge="start" onClick={() => setMobileOpen(true)}><MenuIcon /></IconButton>
          <Typography variant="h6" color="primary" fontWeight={700} sx={{ ml: 1 }}>NutriSense</Typography>
        </Toolbar>
      </AppBar>

      {/* Sidebar */}
      <Box component="nav" sx={{ width: { sm: DRAWER_WIDTH }, flexShrink: { sm: 0 } }}>
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          ModalProps={{ keepMounted: true }}
          sx={{ display: { xs: 'block', sm: 'none' }, '& .MuiDrawer-paper': { width: DRAWER_WIDTH } }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{ display: { xs: 'none', sm: 'block' }, '& .MuiDrawer-paper': { width: DRAWER_WIDTH, boxSizing: 'border-box', borderRight: '1px solid #e8f5e9' } }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      {/* Main content */}
      <Box component="main" sx={{ flex: 1, p: 3, mt: { xs: 7, sm: 0 }, bgcolor: 'background.default', minHeight: '100vh' }}>
        <Outlet />
      </Box>
    </Box>
  )
}
