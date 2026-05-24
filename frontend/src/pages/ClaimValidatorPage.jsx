import React, { useEffect, useState } from 'react'
import {
  Box, Card, CardContent, Typography, Button, CircularProgress,
  TextField, Grid, Chip, Alert, Divider, List, ListItem,
  ListItemText, Accordion, AccordionSummary, AccordionDetails
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import CancelIcon from '@mui/icons-material/Cancel'
import api from '../api/api'

const TODAY = new Date().toISOString().split('T')[0]

export default function ClaimValidatorPage() {
  const [date, setDate]       = useState(TODAY)
  const [claims, setClaims]   = useState([])
  const [selected, setSelected] = useState(null)
  const [result, setResult]   = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')

  useEffect(() => {
    api.get('/analysis/claims').then(r => setClaims(r.data))
  }, [])

  const validate = async () => {
    if (!selected) return
    setLoading(true); setError(''); setResult(null)
    try {
      const { data } = await api.post('/analysis/validate-claim', { claim: selected.key, date })
      setResult(data)
    } catch (e) {
      setError(e.response?.data?.error || 'Validation failed')
    } finally { setLoading(false) }
  }

  return (
    <Box>
      <Typography variant="h5" fontWeight={700} sx={{ mb: 1 }}>Claim Validator</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Uses resolution refutation (proof by contradiction) to validate dietary claims.
      </Typography>

      <Box sx={{ display: 'flex', gap: 2, mb: 3, alignItems: 'center', flexWrap: 'wrap' }}>
        <TextField type="date" label="Date" value={date} onChange={e => setDate(e.target.value)}
          InputLabelProps={{ shrink: true }} size="small" />
      </Box>

      {/* Claim selector */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>Select a Claim to Validate</Typography>
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
          <Button variant="contained" sx={{ mt: 2 }} onClick={validate}
            disabled={!selected || loading}>
            {loading ? <CircularProgress size={20} color="inherit" /> : 'Validate Claim'}
          </Button>
        </CardContent>
      </Card>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {result && (
        <Card>
          <CardContent>
            {/* Verdict */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              {result.valid
                ? <CheckCircleIcon color="success" sx={{ fontSize: 40 }} />
                : <CancelIcon color="error" sx={{ fontSize: 40 }} />}
              <Box>
                <Typography variant="h6">{result.claim_label}</Typography>
                <Chip label={result.valid ? 'VALID — Claim holds' : 'INVALID — Claim does not hold'}
                  color={result.valid ? 'success' : 'error'} />
              </Box>
            </Box>

            <Alert severity={result.valid ? 'success' : 'error'} sx={{ mb: 3 }}>
              {result.explanation}
            </Alert>

            <Divider sx={{ mb: 2 }} />

            {/* KB Clauses */}
            <Typography variant="h6" sx={{ mb: 1 }}>Knowledge Base Clauses (CNF)</Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
              {result.kb_clauses?.map((clause, i) => (
                <Chip key={i} label={`{${clause.join(', ')}}`} size="small" variant="outlined" />
              ))}
            </Box>

            <Typography variant="h6" sx={{ mb: 1 }}>Negated Goal</Typography>
            <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
              {result.negated_goal?.map((clause, i) => (
                <Chip key={i} label={`{${clause.join(', ')}}`} size="small" color="error" variant="outlined" />
              ))}
            </Box>

            {/* Resolution steps */}
            <Typography variant="h6" sx={{ mb: 1 }}>Resolution Steps</Typography>
            {result.steps?.length === 0 && (
              <Typography variant="body2" color="text.secondary">No resolution steps (direct fact check).</Typography>
            )}
            {result.steps?.map((step, i) => (
              <Accordion key={i} disableGutters>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip label={`Step ${step.step}`} size="small" color="primary" variant="outlined" />
                    {step.is_empty
                      ? <Chip label="Empty clause — contradiction!" size="small" color="success" />
                      : <Typography variant="body2">{`{${step.resolvent?.join(', ')}}`}</Typography>}
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography variant="caption" display="block">
                    C1: {`{${step.clause1?.join(', ')}}`}
                  </Typography>
                  <Typography variant="caption" display="block">
                    C2: {`{${step.clause2?.join(', ')}}`}
                  </Typography>
                  <Typography variant="caption" display="block" fontWeight={700}>
                    Resolvent: {step.is_empty ? '∅ (empty clause)' : `{${step.resolvent?.join(', ')}}`}
                  </Typography>
                </AccordionDetails>
              </Accordion>
            ))}
          </CardContent>
        </Card>
      )}
    </Box>
  )
}
