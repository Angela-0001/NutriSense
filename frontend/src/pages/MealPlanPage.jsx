import React, { useEffect, useState } from 'react'
import {
  Box, Card, CardContent, Typography, Button, CircularProgress,
  Grid, Chip, Alert, Divider, LinearProgress, TextField, Accordion,
  AccordionSummary, AccordionDetails, Table, TableBody, TableCell,
  TableHead, TableRow
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import api from '../api/api'

const TODAY = new Date().toISOString().split('T')[0]
const MEAL_LABELS = { breakfast: '🌅 Breakfast', lunch: '☀️ Lunch', dinner: '🌙 Dinner', snack: '🍎 Snack' }

export default function MealPlanPage() {
  const [plan, setPlan]       = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')
  const [weekStart, setWeekStart] = useState(TODAY)

  useEffect(() => {
    api.get('/meal-plan/latest').then(r => { if (r.data) setPlan(r.data) }).catch(() => {})
  }, [])

  const generate = async () => {
    setLoading(true); setError('')
    try {
      const { data } = await api.post('/meal-plan/generate', { week_start: weekStart })
      setPlan(data)
    } catch (e) {
      setError(e.response?.data?.error || 'Generation failed')
    } finally { setLoading(false) }
  }

  const coverage = plan?.nutritional_coverage_percent || plan?.nutritional_coverage || {}
  const coverageEntries = Object.entries(coverage)

  return (
    <Box>
      <Typography variant="h5" fontWeight={700} sx={{ mb: 1 }}>7-Day Meal Plan</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Budget-aware meal plan generated from IFCT 2017 foods, respecting your diet type and monthly budget.
      </Typography>

      <Box sx={{ display: 'flex', gap: 2, mb: 3, alignItems: 'center', flexWrap: 'wrap' }}>
        <TextField type="date" label="Week starting" value={weekStart}
          onChange={e => setWeekStart(e.target.value)} InputLabelProps={{ shrink: true }} size="small" />
        <Button variant="contained" onClick={generate} disabled={loading}>
          {loading ? <CircularProgress size={20} color="inherit" /> : 'Generate Plan'}
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {plan && (
        <>
          {/* Quality report */}
          {plan.quality_report && (
            <Box sx={{ mb: 3, p: 2, bgcolor: plan.quality_report.violations?.length === 0 ? 'success.50' : 'warning.50', borderRadius: 2, border: '1px solid', borderColor: plan.quality_report.violations?.length === 0 ? 'success.light' : 'warning.light' }}>
              <Typography variant="body2" fontWeight={700} color={plan.quality_report.violations?.length === 0 ? 'success.dark' : 'warning.dark'}>
                {plan.quality_report.violations?.length === 0 ? '✅' : '⚠️'} Meal Plan Quality: {plan.quality_report.passed}/{plan.quality_report.total_meals} meals passed all rules
                {plan.quality_report.regenerated > 0 && ` · ${plan.quality_report.regenerated} auto-corrected`}
              </Typography>
              {plan.quality_report.violations?.map((v, i) => (
                <Typography key={i} variant="caption" color="warning.dark" display="block">• {v}</Typography>
              ))}
            </Box>
          )}
          {/* Summary */}
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={6} sm={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="body2" color="text.secondary">Total Cost</Typography>
                  <Typography variant="h5" fontWeight={700} color="primary">
                    ₹{(plan.total_cost_inr || plan.total_cost || 0).toFixed(0)}
                  </Typography>
                  <Typography variant="caption">for 7 days</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="body2" color="text.secondary">Daily Budget</Typography>
                  <Typography variant="h5" fontWeight={700}>
                    ₹{(plan.daily_budget_inr || 0).toFixed(0)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Nutritional coverage */}
          {coverageEntries.length > 0 && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>Avg Daily Nutritional Coverage (% RDA)</Typography>
                <Grid container spacing={2}>
                  {coverageEntries.map(([key, pct]) => (
                    <Grid item xs={12} sm={6} md={4} key={key}>
                      <Box sx={{ mb: 1 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                          <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>{key}</Typography>
                          <Typography variant="body2" fontWeight={600}>{pct}%</Typography>
                        </Box>
                        <LinearProgress variant="determinate" value={Math.min(pct, 100)}
                          color={pct >= 100 ? 'success' : pct >= 60 ? 'warning' : 'error'}
                          sx={{ height: 6, borderRadius: 3 }} />
                      </Box>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          )}

          {/* Day-by-day plan */}
          <Typography variant="h6" sx={{ mb: 2 }}>Daily Meal Plan</Typography>
          {Object.entries(plan.plan || {}).map(([dayDate, dayData]) => (
            <Accordion key={dayDate} disableGutters sx={{ mb: 1 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Typography fontWeight={600}>
                    {new Date(dayDate + 'T00:00:00').toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'short' })}
                  </Typography>
                  <Chip label={`₹${dayData.cost_inr}`} size="small" color="primary" variant="outlined" />
                  <Chip label={`${Math.round(dayData.nutrition?.calories || 0)} kcal`} size="small" variant="outlined" />
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                {Object.entries(dayData.meals || {}).map(([meal, items]) => items.length > 0 && (
                  <Box key={meal} sx={{ mb: 2 }}>
                    <Typography variant="body1" fontWeight={600} sx={{ mb: 1 }}>
                      {MEAL_LABELS[meal] || meal}
                    </Typography>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Food</TableCell>
                          <TableCell align="right">Qty</TableCell>
                          <TableCell align="right">Calories</TableCell>
                          <TableCell align="right">Protein</TableCell>
                          <TableCell align="right">Cost</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {items.map((item, i) => (
                          <TableRow key={i}>
                            <TableCell>{item.food_name}</TableCell>
                            <TableCell align="right">{item.quantity_grams}g</TableCell>
                            <TableCell align="right">{item.nutrition?.calories?.toFixed(0)}</TableCell>
                            <TableCell align="right">{item.nutrition?.protein?.toFixed(1)}g</TableCell>
                            <TableCell align="right">₹{item.cost_inr}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </Box>
                ))}
              </AccordionDetails>
            </Accordion>
          ))}
        </>
      )}
    </Box>
  )
}
