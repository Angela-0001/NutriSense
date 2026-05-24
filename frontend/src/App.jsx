import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { CircularProgress, Box } from '@mui/material'
import { useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import FoodLogPage from './pages/FoodLogPage'
import AnalysisPage from './pages/AnalysisPage'
import BayesianPage from './pages/BayesianPage'
import ClaimValidatorPage from './pages/ClaimValidatorPage'
import DietaryAdvicePage from './pages/DietaryAdvicePage'
import DatasetGenPage from './pages/DatasetGenPage'
import ProfilePage from './pages/ProfilePage'

function PrivateRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return (
    <Box sx={{ display: 'flex', justifyContent: 'center', mt: 10 }}>
      <CircularProgress color="primary" />
    </Box>
  )
  return user ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login"    element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
        <Route index                element={<DashboardPage />} />
        <Route path="log"           element={<FoodLogPage />} />
        <Route path="analysis"      element={<AnalysisPage />} />
        <Route path="bayesian"      element={<BayesianPage />} />
        <Route path="claims"        element={<ClaimValidatorPage />} />
        <Route path="meal-plan"     element={<DietaryAdvicePage />} />
        <Route path="dataset"       element={<DatasetGenPage />} />
        <Route path="profile"       element={<ProfilePage />} />
      </Route>
    </Routes>
  )
}
