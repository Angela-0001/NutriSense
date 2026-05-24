import React, { useEffect, useState } from 'react'
import {
  Box, Card, CardContent, Typography, Button, CircularProgress,
  TextField, Grid, Chip, Alert, Divider, Accordion,
  AccordionSummary, AccordionDetails, Stepper, Step, StepLabel, StepContent
} from '@mui/material'
import ExpandMoreIcon   from '@mui/icons-material/ExpandMore'
import CheckCircleIcon  from '@mui/icons-material/CheckCircle'
import CancelIcon       from '@mui/icons-material/Cancel'
import InfoIcon         from '@mui/icons-material/Info'
import api from '../api/api'

const TODAY = new Date().toISOString().split('T')[0]

// ── Plain-language helpers ────────────────────────────────────────────────────

function humanizeClause(literals) {
  return literals.map(lit => {
    const negated = lit.startsWith('~')
    const key = negated ? lit.slice(1) : lit
    const labels = {
      iron_ok:      'iron intake is adequate',
      protein_ok:   'protein intake is adequate',
      calcium_ok:   'calcium intake is adequate',
      vitD_ok:      'vitamin D intake is adequate',
      vitB12_ok:    'vitamin B12 intake is adequate',
      fibre_ok:     'fibre intake is adequate',
      sugar_ok:     'sugar intake is within safe limits',
      fat_ok:       'fat intake is within safe limits',
      salt_ok:      'salt intake is within safe limits',
      diet_balanced:'overall diet is balanced',
      diabetes_safe:'diet is safe for diabetes risk',
      bp_safe:      'diet is safe for blood pressure',
    }
    const label = labels[key] || key.replace(/_/g, ' ')
    return negated ? `NOT (${label})` : label
  }).join(' OR ')
}

function stepExplanation(step, isLast) {
  const c1 = humanizeClause(step.clause1 || [])
  const c2 = humanizeClause(step.clause2 || [])
  if (step.is_empty) {
    return `Combining "${c1}" with "${c2}" cancels out completely — this is a contradiction. The original claim is therefore PROVED.`
  }
  const result = humanizeClause(step.resolvent || [])
  return `Combining "${c1}" with "${c2}" gives us: "${result}"`
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function ClaimValidatorPage() {
  const [date, setDate]         = useState(TODAY)
  const [claims, setClaims]     = useState([])
  const [selected, setSelected] = useState(null)
  const [result, setResult]     = useState(null)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState('')
  const [showTechnical, setShowTechnical] = useState(false)

  useEffect(() => {
    api.get('/analysis/claims').then(r => setClaims(r.data))
  }, [])

  const validate = async () => {
    if (!selected) return
    setLoading(true); setError(''); setResult(null); setShowTechnical(false)
    try {
      const { data } = await api.post('/analysis/validate-claim', { claim: selected.key, date })
      setResult(data)
    } catch (e) {
      setError(e.response?.data?.error || 'Validation failed')
    } finally { setLoading(false) }
  }

  return (
    <Box>
      <Typography variant="h5" fontWeight={700} sx={{ mb: 0.5 }}>Claim Validator</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Select a claim about your diet and the system will prove or disprove it using logical reasoning.
      </Typography>

      <Box sx={{ display: 'flex', gap: 2, mb: 3, alignItems: 'center' }}>
        <TextField type="date" label="Date" value={date} onChange={e => setDate(e.target.value)}
          InputLabelProps={{ shrink: true }} size="small" />
      </Box>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 1 }}>What would you like to check?</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Pick a claim about your nutrition for the selected date.
          </Typography>
          <Grid container spacing={1}>
            {claims.map(claim => (
              <Grid item key={claim.key}>
                <Chip
                  label={claim.label}
                  onClick={() => setSelected(claim)}
                  variant={selected?.key === claim.key ? 'filled' : 'outlined'}
                  color={selected?.key === claim.key ? 'primary' : 'default'}
                  sx={{ cursor: 'pointer' }}
                />
              </Grid>
            ))}
          </Grid>
          <Button variant="contained" sx={{ mt: 2 }} onClick={validate} disabled={!selected || loading}>
            {loading ? <CircularProgress size={20} color="inherit" /> : 'Check this claim'}
          </Button>
        </CardContent>
      </Card>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {result && (
        <Card>
          <CardContent>

            {/* ── Verdict ── */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              {result.valid
                ? <CheckCircleIcon color="success" sx={{ fontSize: 48 }} />
                : <CancelIcon color="error" sx={{ fontSize: 48 }} />}
              <Box>
                <Typography variant="h5" fontWeight={700}>
                  {result.valid ? '✅ Yes, this is true' : '❌ No, this does not hold'}
                </Typography>
                <Typography variant="body1" color="text.secondary">{result.claim_label}</Typography>
              </Box>
            </Box>

            <Alert severity={result.valid ? 'success' : 'warning'} sx={{ mb: 3 }}>
              {result.valid
                ? `Your ${result.claim_label.toLowerCase()} based on your food log for this date.`
                : `Your ${result.claim_label.toLowerCase()} — your intake does not meet the ICMR recommended daily amount.`}
            </Alert>

            <Divider sx={{ mb: 3 }} />

            {/* ── How the system proved it ── */}
            <Typography variant="h6" sx={{ mb: 0.5 }}>How did the system figure this out?</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              The system uses a technique called <strong>Resolution Refutation</strong> — it assumes the opposite of your claim is true, then tries to find a logical contradiction. If it finds one, your original claim is proved.
            </Typography>

            {/* Step-by-step in plain English */}
            <Stepper orientation="vertical" sx={{ mb: 2 }}>
              <Step active completed>
                <StepLabel>Step 1 — Check your actual intake</StepLabel>
                <StepContent>
                  <Typography variant="body2">
                    The system looked at your food log for {date} and compared your intake against the ICMR Recommended Daily Allowance (RDA).
                  </Typography>
                  <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {result.kb_clauses?.map((clause, i) => (
                      <Chip key={i} size="small" variant="outlined"
                        color={clause.some(l => l.startsWith('~')) ? 'error' : 'success'}
                        label={humanizeClause(clause)} />
                    ))}
                  </Box>
                </StepContent>
              </Step>

              <Step active completed>
                <StepLabel>Step 2 — Assume the opposite</StepLabel>
                <StepContent>
                  <Typography variant="body2">
                    To prove your claim, the system temporarily assumes it is <strong>false</strong> and tries to find a contradiction.
                  </Typography>
                  <Box sx={{ mt: 1, display: 'flex', gap: 0.5 }}>
                    {result.negated_goal?.map((clause, i) => (
                      <Chip key={i} size="small" color="warning" variant="outlined"
                        label={`Assuming: ${humanizeClause(clause)}`} />
                    ))}
                  </Box>
                </StepContent>
              </Step>

              <Step active completed>
                <StepLabel>
                  Step 3 — {result.valid ? 'Contradiction found → claim is TRUE' : 'No contradiction → claim is FALSE'}
                </StepLabel>
                <StepContent>
                  {result.steps?.length === 0 ? (
                    <Typography variant="body2">The fact was directly known — no further steps needed.</Typography>
                  ) : (
                    result.steps?.map((step, i) => (
                      <Box key={i} sx={{ mb: 1, p: 1.5, bgcolor: step.is_empty ? 'success.50' : 'action.hover', borderRadius: 2, border: '1px solid', borderColor: step.is_empty ? 'success.light' : 'divider' }}>
                        <Typography variant="body2" fontWeight={600} color={step.is_empty ? 'success.dark' : 'text.primary'}>
                          {step.is_empty ? '🎯 Contradiction found!' : `Resolution ${step.step}`}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                          {stepExplanation(step)}
                        </Typography>
                      </Box>
                    ))
                  )}
                </StepContent>
              </Step>
            </Stepper>

            {/* ── Technical details toggle ── */}
            <Button size="small" startIcon={<InfoIcon />} onClick={() => setShowTechnical(t => !t)}
              sx={{ mb: 1 }} color="inherit">
              {showTechnical ? 'Hide' : 'Show'} technical details (CNF notation)
            </Button>

            {showTechnical && (
              <Box sx={{ p: 2, bgcolor: 'action.hover', borderRadius: 2 }}>
                <Typography variant="caption" fontWeight={700} display="block" sx={{ mb: 1 }}>
                  Knowledge Base Clauses (CNF):
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
                  {result.kb_clauses?.map((clause, i) => (
                    <Chip key={i} label={`{${clause.join(', ')}}`} size="small" variant="outlined" />
                  ))}
                </Box>
                <Typography variant="caption" fontWeight={700} display="block" sx={{ mb: 1 }}>
                  Negated Goal:
                </Typography>
                <Box sx={{ display: 'flex', gap: 0.5, mb: 2 }}>
                  {result.negated_goal?.map((clause, i) => (
                    <Chip key={i} label={`{${clause.join(', ')}}`} size="small" color="error" variant="outlined" />
                  ))}
                </Box>
                {result.steps?.map((step, i) => (
                  <Accordion key={i} disableGutters>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip label={`Step ${step.step}`} size="small" color="primary" variant="outlined" />
                        {step.is_empty
                          ? <Chip label="Empty clause ∅ — contradiction!" size="small" color="success" />
                          : <Typography variant="body2">{`{${step.resolvent?.join(', ')}}`}</Typography>}
                      </Box>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Typography variant="caption" display="block">C1: {`{${step.clause1?.join(', ')}}`}</Typography>
                      <Typography variant="caption" display="block">C2: {`{${step.clause2?.join(', ')}}`}</Typography>
                      <Typography variant="caption" display="block" fontWeight={700}>
                        Resolvent: {step.is_empty ? '∅ (empty clause)' : `{${step.resolvent?.join(', ')}}`}
                      </Typography>
                    </AccordionDetails>
                  </Accordion>
                ))}
              </Box>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  )
}
