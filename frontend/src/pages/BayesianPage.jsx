import React, { useState } from 'react'
import {
  Box, Card, CardContent, Typography, Button, CircularProgress,
  TextField, Grid, LinearProgress, Chip, Alert, Divider, List,
  ListItem, ListItemText
} from '@mui/material'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import api from '../api/api'

const TODAY = new Date().toISOString().split('T')[0]

const LEVEL_COLOR = { Low: '#4caf50', Moderate: '#ff9800', High: '#f44336', Critical: '#b71c1c' }

export default function BayesianPage() {
  const [date, setDate]     = useState(TODAY)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]   = useState('')

  const run = async () => {
    setLoading(true); setError('')
    try {
      const { data } = await api.get(`/analysis/bayesian?date=${date}`)
      setResult(data)
    } catch (e) {
      setError(e.response?.data?.error || 'Analysis failed')
    } finally { setLoading(false) }
  }

  const chartData = result?.risks?.map(r => ({
    name: r.disease.replace('Hypertension (High BP)', 'Hypertension').replace('Vitamin D Deficiency', 'Vit D Def.'),
    probability: Math.round(r.risk_probability * 100),
    level: r.risk_level,
    color: LEVEL_COLOR[r.risk_level] || '#9e9e9e'
  })) || []

  return (
    <Box>
      <Typography variant="h5" fontWeight={700} sx={{ mb: 1 }}>Bayesian Disease Risk</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Probabilistic disease risk prediction using a Bayesian Network with ICMR-based CPTs.
      </Typography>

      <Box sx={{ display: 'flex', gap: 2, mb: 3, alignItems: 'center' }}>
        <TextField type="date" label="Date" value={date} onChange={e => setDate(e.target.value)}
          InputLabelProps={{ shrink: true }} size="small" />
        <Button variant="contained" onClick={run} disabled={loading}>
          {loading ? <CircularProgress size={20} color="inherit" /> : 'Run Bayesian Inference'}
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {result && (
        <Grid container spacing={3}>
          {/* Bar chart */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>Risk Probabilities</Typography>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                    <YAxis domain={[0, 100]} tickFormatter={v => `${v}%`} />
                    <Tooltip formatter={v => `${v}%`} />
                    <Bar dataKey="probability" radius={[6, 6, 0, 0]}>
                      {chartData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>

          {/* Risk cards */}
          {result.risks.map(risk => (
            <Grid item xs={12} sm={6} md={4} key={risk.disease}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="h6" sx={{ fontSize: 15 }}>{risk.disease}</Typography>
                    <Chip label={risk.risk_level} size="small"
                      sx={{ bgcolor: LEVEL_COLOR[risk.risk_level], color: 'white', fontWeight: 700 }} />
                  </Box>

                  <Box sx={{ mb: 1.5 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="body2">Risk probability</Typography>
                      <Typography variant="body2" fontWeight={700}>
                        {(risk.risk_probability * 100).toFixed(1)}%
                      </Typography>
                    </Box>
                    <LinearProgress variant="determinate"
                      value={risk.risk_probability * 100}
                      sx={{ height: 8, borderRadius: 4,
                        '& .MuiLinearProgress-bar': { bgcolor: LEVEL_COLOR[risk.risk_level] } }} />
                  </Box>

                  {risk.main_contributing_factors?.length > 0 && (
                    <>
                      <Typography variant="caption" fontWeight={600} color="text.secondary">Contributing factors:</Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5, mb: 1 }}>
                        {risk.main_contributing_factors.map(f => (
                          <Chip key={f} label={f} size="small" color="error" variant="outlined" />
                        ))}
                      </Box>
                    </>
                  )}

                  {risk.dietary_changes?.length > 0 && (
                    <>
                      <Divider sx={{ my: 1 }} />
                      <Typography variant="caption" fontWeight={600}>Dietary changes:</Typography>
                      <List dense disablePadding>
                        {risk.dietary_changes.slice(0, 3).map((c, i) => (
                          <ListItem key={i} disablePadding sx={{ py: 0.2 }}>
                            <ListItemText primary={`• ${c}`} primaryTypographyProps={{ variant: 'caption' }} />
                          </ListItem>
                        ))}
                      </List>
                    </>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  )
}
