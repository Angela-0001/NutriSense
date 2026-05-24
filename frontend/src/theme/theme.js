import { createTheme } from '@mui/material/styles'

const theme = createTheme({
  palette: {
    mode: 'light',
    primary:   { main: '#2e7d32', light: '#60ad5e', dark: '#005005' },
    secondary: { main: '#f57c00', light: '#ffad42', dark: '#bb4d00' },
    background: { default: '#f5f7f5', paper: '#ffffff' },
    error:   { main: '#d32f2f' },
    warning: { main: '#f57c00' },
    success: { main: '#388e3c' },
    info:    { main: '#0288d1' },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", sans-serif',
    h4: { fontWeight: 700 },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
  },
  shape: { borderRadius: 12 },
  components: {
    MuiCard: {
      styleOverrides: {
        root: { boxShadow: '0 2px 12px rgba(0,0,0,0.08)', borderRadius: 16 }
      }
    },
    MuiButton: {
      styleOverrides: {
        root: { borderRadius: 8, textTransform: 'none', fontWeight: 600 }
      }
    },
    MuiChip: {
      styleOverrides: { root: { borderRadius: 8 } }
    }
  }
})

export default theme
