import React, { useState } from 'react'
import {
  Box, Card, CardContent, Typography, Button, CircularProgress,
  Grid, Chip, Alert, LinearProgress, Divider, List, ListItem,
  ListItemText, Accordion, AccordionSummary, AccordionDetails,
  Table, TableHead, TableBody, TableRow, TableCell
} from '@mui/material'
import ExpandMoreIcon       from '@mui/icons-material/ExpandMore'
import CheckCircleIcon      from '@mui/icons-material/CheckCircle'
import WarningAmberIcon     from '@mui/icons-material/WarningAmber'
import TipsAndUpdatesIcon   from '@mui/icons-material/TipsAndUpdates'
import RestaurantMenuIcon   from '@mui/icons-material/RestaurantMenu'
import api from '../api/api'

const SEVERITY_COLOR = { critical: 'error', high: 'error', moderate: 'warning', mild: 'info' }

export default function DietaryAdvicePage() {
  const [result, setResult]   = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')

  const fetchAdvice = async () => {
    setLoading(true); setError(''); setResult(null)
    try {
      const { data } = await api.get('/analysis/dietary-advice')
      setResult(data)
    } catch (e) {
      setError(e.response?.data?.error || 'Failed to load advice')
    } finally { setLoading(false) }
  }

  return (
    <Box>
      <Typography variant="h5" fontWeight={700} sx={{ mb: 0.5 }}>Dietary Advice</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Based on your last 7 days of food logs, here's what to include more in your diet.
      </Typography>

      <Button variant="contained" onClick={fetchAdvice} disabled={loading} sx={{ mb: 3 }}>
        {loading ? <CircularProgress size={20} color="inherit" /> : 'Analyse My Diet'}
      </Button>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {result && (
        <Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Analysis based on <strong>{result.days_analysed} day{result.days_analysed !== 1 ? 's' : ''}</strong> of food logs.
          </Typography>

          {/* What's going well */}
          {result.adequate_nutrients?.length > 0 && (
            <Card sx={{ mb: 3, border: '1px solid', borderColor: 'success.light' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                  <CheckCircleIcon color="success" />
                  <Typography variant="h6" color="success.dark">What you're doing well</Typography>
                </Box>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {result.adequate_nutrients.map(n => (
                    <Chip key={n.nutrient}
                      label={`${n.nutrient} — ${n.percent_of_rda}% of RDA`}
                      color="success" variant="outlined" size="small" />
                  ))}
                </Box>
              </CardContent>
            </Card>
          )}

          {result.deficiencies?.length === 0 && (
            <Alert severity="success" sx={{ mb: 3 }}>
              Your diet looks well-balanced! No significant deficiencies detected in the last {result.days_analysed} days.
            </Alert>
          )}

          {/* Deficiency advice cards */}
          {result.deficiencies?.map(d => (
            <Card key={d.deficiency_type} sx={{ mb: 3, border: '1px solid', borderColor: d.severity === 'critical' || d.severity === 'high' ? 'error.light' : 'warning.light' }}>
              <CardContent>
                {/* Header */}
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <WarningAmberIcon color={SEVERITY_COLOR[d.severity] || 'warning'} />
                    <Box>
                      <Typography variant="h6">{d.nutrient} is low</Typography>
                      <Typography variant="body2" color="text.secondary">
                        You're getting <strong>{d.percent_of_rda}%</strong> of your daily requirement
                        ({d.current_avg?.toFixed?.(1)} vs {d.rda} needed)
                      </Typography>
                    </Box>
                  </Box>
                  <Chip label={d.severity} color={SEVERITY_COLOR[d.severity] || 'warning'} size="small" />
                </Box>

                {/* Progress bar */}
                <Box sx={{ mb: 2 }}>
                  <LinearProgress
                    variant="determinate"
                    value={Math.min(d.percent_of_rda, 100)}
                    color={d.percent_of_rda < 50 ? 'error' : 'warning'}
                    sx={{ height: 10, borderRadius: 5 }}
                  />
                  <Typography variant="caption" color="text.secondary">
                    Need {d.gap} more per day on average
                  </Typography>
                </Box>

                {/* Why it matters */}
                <Alert severity="info" icon={false} sx={{ mb: 2 }}>
                  <Typography variant="body2">{d.why}</Typography>
                </Alert>

                {/* Foods to add */}
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <RestaurantMenuIcon color="primary" fontSize="small" />
                  <Typography variant="body1" fontWeight={700}>Add these to your diet</Typography>
                </Box>
                <Table size="small" sx={{ mb: 2 }}>
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>Food</strong></TableCell>
                      <TableCell><strong>How much</strong></TableCell>
                      <TableCell><strong>When to eat</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {d.foods_to_add?.map((food, i) => (
                      <TableRow key={i}>
                        <TableCell>{food.name}</TableCell>
                        <TableCell>
                          <Typography variant="body2">{food.amount}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {Object.entries(food)
                              .filter(([k]) => !['name','amount','meal'].includes(k))
                              .map(([k, v]) => `${k}: ${v}`)
                              .join(' · ')}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" color="primary.main">{food.meal}</Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>

                {/* Tip */}
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, mb: 2, p: 1.5, bgcolor: 'primary.50', borderRadius: 2 }}>
                  <TipsAndUpdatesIcon color="primary" fontSize="small" sx={{ mt: 0.3 }} />
                  <Typography variant="body2">{d.tip}</Typography>
                </Box>

                {/* Avoid + weekly goal */}
                <Grid container spacing={2}>
                  {d.avoid?.length > 0 && (
                    <Grid item xs={12} sm={6}>
                      <Typography variant="body2" fontWeight={700} color="error.main" sx={{ mb: 0.5 }}>
                        ⚠️ Avoid or reduce
                      </Typography>
                      <List dense disablePadding>
                        {d.avoid.map((a, i) => (
                          <ListItem key={i} disablePadding>
                            <ListItemText primary={`• ${a}`} primaryTypographyProps={{ variant: 'body2' }} />
                          </ListItem>
                        ))}
                      </List>
                    </Grid>
                  )}
                  {d.weekly_goal && (
                    <Grid item xs={12} sm={6}>
                      <Typography variant="body2" fontWeight={700} color="success.dark" sx={{ mb: 0.5 }}>
                        🎯 Weekly goal
                      </Typography>
                      <Typography variant="body2">{d.weekly_goal}</Typography>
                    </Grid>
                  )}
                </Grid>
              </CardContent>
            </Card>
          ))}
        </Box>
      )}
    </Box>
  )
}
