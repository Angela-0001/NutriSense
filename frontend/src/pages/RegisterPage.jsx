import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import {
  Box, Card, CardContent, TextField, Button, Typography, Alert,
  CircularProgress, MenuItem, Grid
} from '@mui/material'
import { useAuth } from '../context/AuthContext'

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    name: '', email: '', password: '', age: '', gender: 'female',
    weight_kg: '', height_cm: '', diet_type: 'veg', budget_monthly_inr: 3000
  })
  const [error, setError]     = useState('')
  const [loading, setLoading] = useState(false)

  const set = (k, v) => setForm(p => ({ ...p, [k]: v }))

  const handleSubmit = async e => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register({ ...form, age: Number(form.age), weight_kg: Number(form.weight_kg), height_cm: Number(form.height_cm) })
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.error || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'background.default', py: 4 }}>
      <Card sx={{ width: '100%', maxWidth: 500, p: 2 }}>
        <CardContent>
          <Typography variant="h5" color="primary" fontWeight={700} sx={{ mb: 3 }}>Create Account</Typography>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <Box component="form" onSubmit={handleSubmit}>
            <Grid container spacing={2}>
              <Grid item xs={12}><TextField label="Full Name" value={form.name} onChange={e => set('name', e.target.value)} required fullWidth /></Grid>
              <Grid item xs={12}><TextField label="Email" type="email" value={form.email} onChange={e => set('email', e.target.value)} required fullWidth /></Grid>
              <Grid item xs={12}><TextField label="Password" type="password" value={form.password} onChange={e => set('password', e.target.value)} required fullWidth /></Grid>
              <Grid item xs={6}><TextField label="Age" type="number" value={form.age} onChange={e => set('age', e.target.value)} fullWidth /></Grid>
              <Grid item xs={6}>
                <TextField select label="Gender" value={form.gender} onChange={e => set('gender', e.target.value)} fullWidth>
                  {['male','female','other'].map(g => <MenuItem key={g} value={g}>{g}</MenuItem>)}
                </TextField>
              </Grid>
              <Grid item xs={6}><TextField label="Weight (kg)" type="number" value={form.weight_kg} onChange={e => set('weight_kg', e.target.value)} fullWidth /></Grid>
              <Grid item xs={6}><TextField label="Height (cm)" type="number" value={form.height_cm} onChange={e => set('height_cm', e.target.value)} fullWidth /></Grid>
              <Grid item xs={6}>
                <TextField select label="Diet Type" value={form.diet_type} onChange={e => set('diet_type', e.target.value)} fullWidth>
                  {['veg','nonveg','eggetarian','vegan'].map(d => <MenuItem key={d} value={d}>{d}</MenuItem>)}
                </TextField>
              </Grid>
              <Grid item xs={6}><TextField label="Monthly Budget (₹)" type="number" value={form.budget_monthly_inr} onChange={e => set('budget_monthly_inr', e.target.value)} fullWidth /></Grid>
              <Grid item xs={12}>
                <Button type="submit" variant="contained" size="large" disabled={loading} fullWidth>
                  {loading ? <CircularProgress size={22} color="inherit" /> : 'Register'}
                </Button>
              </Grid>
            </Grid>
          </Box>
          <Typography variant="body2" sx={{ mt: 2, textAlign: 'center' }}>
            Already have an account? <Link to="/login" style={{ color: 'inherit', fontWeight: 600 }}>Sign in</Link>
          </Typography>
        </CardContent>
      </Card>
    </Box>
  )
}
