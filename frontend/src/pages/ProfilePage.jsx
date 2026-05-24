import React, { useState } from 'react'
import {
  Box, Card, CardContent, Typography, TextField, Button,
  MenuItem, Grid, Alert, CircularProgress, Divider, Chip
} from '@mui/material'
import { useAuth } from '../context/AuthContext'

export default function ProfilePage() {
  const { user, updateProfile, logout } = useAuth()
  const [form, setForm] = useState({
    name:               user?.name || '',
    age:                user?.age || '',
    gender:             user?.gender || 'female',
    weight_kg:          user?.weight_kg || '',
    height_cm:          user?.height_cm || '',
    diet_type:          user?.diet_type || 'veg',
    budget_monthly_inr: user?.budget_monthly_inr || 3000,
  })
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')

  const set = (k, v) => setForm(p => ({ ...p, [k]: v }))

  const handleSave = async () => {
    setLoading(true); setError(''); setSuccess(false)
    try {
      await updateProfile({ ...form, age: Number(form.age), weight_kg: Number(form.weight_kg), height_cm: Number(form.height_cm) })
      setSuccess(true)
    } catch (e) {
      setError(e.response?.data?.error || 'Update failed')
    } finally { setLoading(false) }
  }

  const bmi = user?.bmi

  return (
    <Box>
      <Typography variant="h5" fontWeight={700} sx={{ mb: 3 }}>Profile</Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Box sx={{ width: 80, height: 80, borderRadius: '50%', bgcolor: 'primary.main',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                mx: 'auto', mb: 2, fontSize: 32, color: 'white', fontWeight: 700 }}>
                {user?.name?.[0]?.toUpperCase()}
              </Box>
              <Typography variant="h6" fontWeight={700}>{user?.name}</Typography>
              <Typography variant="body2" color="text.secondary">{user?.email}</Typography>
              <Divider sx={{ my: 2 }} />
              <Box sx={{ display: 'flex', justifyContent: 'space-around' }}>
                <Box>
                  <Typography variant="h6" fontWeight={700}>{user?.age || '—'}</Typography>
                  <Typography variant="caption" color="text.secondary">Age</Typography>
                </Box>
                <Box>
                  <Typography variant="h6" fontWeight={700}>{bmi || '—'}</Typography>
                  <Typography variant="caption" color="text.secondary">BMI</Typography>
                </Box>
                <Box>
                  <Typography variant="h6" fontWeight={700}>{user?.diet_type}</Typography>
                  <Typography variant="caption" color="text.secondary">Diet</Typography>
                </Box>
              </Box>
              <Divider sx={{ my: 2 }} />
              <Chip label={`Budget: ₹${user?.budget_monthly_inr}/mo`} color="primary" variant="outlined" />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Edit Profile</Typography>
              {success && <Alert severity="success" sx={{ mb: 2 }}>Profile updated.</Alert>}
              {error   && <Alert severity="error"   sx={{ mb: 2 }}>{error}</Alert>}
              <Grid container spacing={2}>
                <Grid item xs={12}><TextField label="Full Name" value={form.name} onChange={e => set('name', e.target.value)} fullWidth /></Grid>
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
                  <Button variant="contained" onClick={handleSave} disabled={loading}>
                    {loading ? <CircularProgress size={20} color="inherit" /> : 'Save Changes'}
                  </Button>
                  <Button variant="outlined" color="error" sx={{ ml: 2 }} onClick={logout}>
                    Logout
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
