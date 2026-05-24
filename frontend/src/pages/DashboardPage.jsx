import React, { useEffect, useState } from 'react'
import {
  Box, Grid, Card, CardContent, Typography, CircularProgress,
  Chip, Alert, Button
} from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip } from 'recharts'
import { useAuth } from '../context/AuthContext'
import api from '../api/api'
import NutrientBar from '../components/NutrientBar'

const TODAY = new Date().toISOString().split('T')[0]

export default function DashboardPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [daily, setDaily]       = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading]   = useState(true)

  useEffect(() => {
    Promise.all([
      api.get(`/logs/daily?date=${TODAY}`),
      api.get(`/analysis/full?date=${TODAY}`)
    ]).then(([d, a]) => {
      setDaily(d.data)
      setAnalysis(a.data)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}><CircularProgress /></Box>

  const rda = analysis?.rda || {}
  const nutrition = analysis?.nutrition || {}

  const radarData = [
    { nutrient: 'Protein',   value: rda.protein   ? Math.min((nutrition.protein   / rda.protein)   * 100, 120) : 0 },
    { nutrient: 'Iron',      value: rda.iron       ? Math.min((nutrition.iron      / rda.iron)       * 100, 120) : 0 },
    { nutrient: 'Calcium',   value: rda.calcium    ? Math.min((nutrition.calcium   / rda.calcium)    * 100, 120) : 0 },
    { nutrient: 'Vit D',     value: rda.vitaminD   ? Math.min((nutrition.vitaminD  / rda.vitaminD)   * 100, 120) : 0 },
    { nutrient: 'Vit B12',   value: rda.vitaminB12 ? Math.min((nutrition.vitaminB12/ rda.vitaminB12) * 100, 120) : 0 },
    { nutrient: 'Fibre',     value: rda.fibre      ? Math.min((nutrition.fibre     / rda.fibre)      * 100, 120) : 0 },
  ]

  const deficiencies = analysis?.deficiencies || []
  const risks        = analysis?.risks || []

  return (
    <Box>
      <Typography variant="h5" fontWeight={700} sx={{ mb: 0.5 }}>
        Good {getGreeting()}, {user?.name?.split(' ')[0]} 👋
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Here's your nutrition snapshot for today.
      </Typography>

      {!daily && (
        <Alert severity="info" sx={{ mb: 3 }} action={
          <Button size="small" onClick={() => navigate('/log')}>Log Food</Button>
        }>
          No food logged today. Start logging to see your analysis.
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Calorie card */}
        <Grid item xs={12} sm={6} md={3}>
          <StatCard label="Calories" value={`${Math.round(nutrition.calories || 0)} kcal`}
            sub={`Goal: ${rda.calories || 2000} kcal`} color="#2e7d32" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard label="Protein" value={`${(nutrition.protein || 0).toFixed(1)}g`}
            sub={`RDA: ${rda.protein || 55}g`} color="#1565c0" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard label="Iron" value={`${(nutrition.iron || 0).toFixed(1)}mg`}
            sub={`RDA: ${rda.iron || 21}mg`} color="#b71c1c" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard label="Deficiencies" value={deficiencies.length}
            sub={deficiencies.length === 0 ? 'All good!' : 'detected today'} color="#e65100" />
        </Grid>

        {/* Nutrient bars */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Today's Nutrients vs RDA</Typography>
              <NutrientBar label="Protein"    value={nutrition.protein || 0}    rda={rda.protein || 55}    unit="g" />
              <NutrientBar label="Iron"       value={nutrition.iron || 0}       rda={rda.iron || 21}       unit="mg" />
              <NutrientBar label="Calcium"    value={nutrition.calcium || 0}    rda={rda.calcium || 600}   unit="mg" />
              <NutrientBar label="Vitamin D"  value={nutrition.vitaminD || 0}   rda={rda.vitaminD || 10}   unit="mcg" />
              <NutrientBar label="Vitamin B12"value={nutrition.vitaminB12 || 0} rda={rda.vitaminB12 || 1}  unit="mcg" />
              <NutrientBar label="Fibre"      value={nutrition.fibre || 0}      rda={rda.fibre || 35}      unit="g" />
            </CardContent>
          </Card>
        </Grid>

        {/* Radar chart */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 1 }}>Nutrient Coverage (%)</Typography>
              <ResponsiveContainer width="100%" height={260}>
                <RadarChart data={radarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="nutrient" tick={{ fontSize: 12 }} />
                  <Radar dataKey="value" stroke="#2e7d32" fill="#2e7d32" fillOpacity={0.25} />
                  <Tooltip formatter={v => `${v.toFixed(0)}%`} />
                </RadarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Deficiency alerts */}
        {deficiencies.length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>⚠️ Deficiencies Detected</Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {deficiencies.map(d => (
                    <Chip key={d.type} label={d.name} color="error" variant="outlined"
                      onClick={() => navigate('/analysis')} />
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Disease risks */}
        {risks.length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>🔴 Disease Risks</Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {risks.map(r => (
                    <Chip key={r.type} label={r.name} color="warning" variant="outlined"
                      onClick={() => navigate('/bayesian')} />
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  )
}

function StatCard({ label, value, sub, color }) {
  return (
    <Card>
      <CardContent>
        <Typography variant="body2" color="text.secondary">{label}</Typography>
        <Typography variant="h4" fontWeight={700} sx={{ color, my: 0.5 }}>{value}</Typography>
        <Typography variant="caption" color="text.secondary">{sub}</Typography>
      </CardContent>
    </Card>
  )
}

function getGreeting() {
  const h = new Date().getHours()
  if (h < 12) return 'morning'
  if (h < 17) return 'afternoon'
  return 'evening'
}
