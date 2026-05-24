import React, { useState } from 'react'
import {
  Box, Card, CardContent, Typography, Button, CircularProgress,
  TextField, Chip, Accordion, AccordionSummary, AccordionDetails,
  Alert, Divider, List, ListItem, ListItemText, Grid, Tab, Tabs
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import api from '../api/api'

const TODAY = new Date().toISOString().split('T')[0]

export default function AnalysisPage() {
  const [date, setDate]       = useState(TODAY)
  const [tab, setTab]         = useState(0)
  const [fcResult, setFcResult] = useState(null)
  const [bcGoal, setBcGoal]   = useState('anaemia_risk')
  const [bcResult, setBcResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')

  const runFC = async () => {
    setLoading(true); setError('')
    try {
      const { data } = await api.get(`/analysis/forward-chain?date=${date}`)
      setFcResult(data)
    } catch (e) {
      setError(e.response?.data?.error || 'Analysis failed')
    } finally { setLoading(false) }
  }

  const runBC = async () => {
    setLoading(true); setError('')
    try {
      const { data } = await api.post('/analysis/backward-chain', { goal: bcGoal, date })
      setBcResult(data)
    } catch (e) {
      setError(e.response?.data?.error || 'Analysis failed')
    } finally { setLoading(false) }
  }

  const severityColor = s => ({ critical: 'error', high: 'error', moderate: 'warning', mild: 'info', positive: 'success' }[s] || 'default')

  return (
    <Box>
      <Typography variant="h5" fontWeight={700} sx={{ mb: 1 }}>Nutritional Analysis</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Forward chaining detects deficiencies. Backward chaining explains why.
      </Typography>

      <Box sx={{ display: 'flex', gap: 2, mb: 3, alignItems: 'center', flexWrap: 'wrap' }}>
        <TextField type="date" label="Date" value={date} onChange={e => setDate(e.target.value)}
          InputLabelProps={{ shrink: true }} size="small" />
      </Box>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 3 }}>
        <Tab label="Forward Chaining" />
        <Tab label="Backward Chaining" />
      </Tabs>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {/* ── FORWARD CHAINING ── */}
      {tab === 0 && (
        <Box>
          <Button variant="contained" onClick={runFC} disabled={loading} sx={{ mb: 3 }}>
            {loading ? <CircularProgress size={20} color="inherit" /> : 'Run Forward Chaining'}
          </Button>

          {fcResult && (
            <Grid container spacing={3}>
              <Grid item xs={12} sm={4}>
                <Card>
                  <CardContent>
                    <Typography variant="body2" color="text.secondary">Rules Fired</Typography>
                    <Typography variant="h4" fontWeight={700} color="primary">{fcResult.rules_fired}</Typography>
                    <Typography variant="caption">in {fcResult.iterations} iteration(s)</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Card>
                  <CardContent>
                    <Typography variant="body2" color="text.secondary">Deficiencies</Typography>
                    <Typography variant="h4" fontWeight={700} color="error.main">{fcResult.deficiencies.length}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Card>
                  <CardContent>
                    <Typography variant="body2" color="text.secondary">Disease Risks</Typography>
                    <Typography variant="h4" fontWeight={700} color="warning.main">{fcResult.risks.length}</Typography>
                  </CardContent>
                </Card>
              </Grid>

              {/* Deficiency cards */}
              {fcResult.deficiencies.map(d => (
                <Grid item xs={12} md={6} key={d.type}>
                  <Card>
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="h6">{d.name}</Typography>
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          <Chip label={d.severity} color={severityColor(d.severity)} size="small" />
                          {d.data_confidence?.has_ai_estimated_foods && (
                            <Chip label="~AI data" size="small" color="warning" variant="outlined" />
                          )}
                        </Box>
                      </Box>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>{d.health_impact}</Typography>

                      {d.data_confidence?.has_ai_estimated_foods && (
                        <Alert severity="warning" sx={{ mb: 1.5, py: 0.5 }}>
                          <Typography variant="caption">{d.data_confidence.accuracy_note}</Typography>
                        </Alert>
                      )}

                      <Typography variant="body2" fontWeight={600} sx={{ mb: 0.5 }}>Recommended foods:</Typography>
                      {d.recommended_foods_context ? (
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.75 }}>
                          {d.recommended_foods_context.map((rec, i) => (
                            <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Chip
                                label={rec.prepared_name}
                                size="small"
                                color={rec.has_specific_form ? 'primary' : 'default'}
                                variant={rec.has_specific_form ? 'filled' : 'outlined'}
                              />
                              {rec.prepared_name !== rec.raw_ingredient && (
                                <Typography variant="caption" color="text.secondary">
                                  ({rec.raw_ingredient})
                                </Typography>
                              )}
                              {!rec.has_specific_form && (
                                <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                                  — {rec.cooking_note}
                                </Typography>
                              )}
                            </Box>
                          ))}
                        </Box>
                      ) : (
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {d.recommended_foods.map(f => <Chip key={f} label={f} size="small" variant="outlined" />)}
                        </Box>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              ))}

              {/* Reasoning chain */}
              <Grid item xs={12}>
                <Typography variant="h6" sx={{ mb: 1 }}>Reasoning Chain</Typography>
                {fcResult.reasoning_chain.map((step, i) => (
                  <Accordion key={i} disableGutters>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip label={`Step ${step.step}`} size="small" color="primary" variant="outlined" />
                        <Typography variant="body2" fontWeight={600}>{step.rule_name}</Typography>
                        <Chip label={step.severity} size="small" color={severityColor(step.severity)} />
                      </Box>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Typography variant="body2" sx={{ mb: 1 }}>{step.explanation}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        Conclusion: <strong>{step.conclusion}</strong> = {String(step.conclusion_value)}
                      </Typography>
                      <Divider sx={{ my: 1 }} />
                      <Typography variant="caption" fontWeight={600}>Conditions matched:</Typography>
                      {step.conditions_matched.map((c, j) => (
                        <Typography key={j} variant="caption" display="block" sx={{ ml: 1 }}>
                          • {c.fact} {c.op} {c.threshold} (actual: {c.actual_value?.toFixed?.(2) ?? c.actual_value})
                        </Typography>
                      ))}
                    </AccordionDetails>
                  </Accordion>
                ))}
              </Grid>
            </Grid>
          )}
        </Box>
      )}

      {/* ── BACKWARD CHAINING ── */}
      {tab === 1 && (
        <Box>
          <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap', alignItems: 'center' }}>
            <TextField select label="Goal to prove" value={bcGoal} onChange={e => setBcGoal(e.target.value)} size="small" sx={{ minWidth: 220 }}>
              {['anaemia_risk','diabetes_risk','bp_risk','osteoporosis_risk',
                'iron_deficiency','protein_deficiency','calcium_deficiency',
                'vitD_deficiency','vitB12_deficiency'].map(g => (
                <option key={g} value={g} style={{ padding: 8 }}>{g.replace(/_/g, ' ')}</option>
              ))}
            </TextField>
            <Button variant="contained" onClick={runBC} disabled={loading}>
              {loading ? <CircularProgress size={20} color="inherit" /> : 'Prove Goal'}
            </Button>
          </Box>

          {bcResult && (
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Typography variant="h6">Goal: {bcResult.goal.replace(/_/g, ' ')}</Typography>
                  <Chip label={bcResult.proved ? 'PROVED ✓' : 'NOT PROVED ✗'}
                    color={bcResult.proved ? 'success' : 'error'} />
                </Box>
                <Alert severity={bcResult.proved ? 'error' : 'success'} sx={{ mb: 2 }}>
                  {bcResult.explanation}
                </Alert>
                <Typography variant="h6" sx={{ mb: 1 }}>Proof Steps</Typography>
                <List dense>
                  {bcResult.proof_steps.map((step, i) => (
                    <ListItem key={i} sx={{ borderLeft: '3px solid', borderColor: step.proved ? 'success.main' : 'error.main', mb: 0.5, pl: 2 }}>
                      <ListItemText
                        primary={`Step ${step.step}: [${step.type}] ${step.goal}`}
                        secondary={step.reason || step.explanation || ''}
                        primaryTypographyProps={{ variant: 'body2', fontWeight: 600 }}
                        secondaryTypographyProps={{ variant: 'caption' }}
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          )}
        </Box>
      )}
    </Box>
  )
}
