import React, { useState } from 'react'
import {
  Box, Card, CardContent, Typography, TextField, Button, Chip,
  CircularProgress, Alert, Table, TableHead, TableBody, TableRow,
  TableCell, Checkbox, Tooltip, Grid
} from '@mui/material'
import DownloadIcon    from '@mui/icons-material/Download'
import SaveIcon        from '@mui/icons-material/Save'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import api from '../api/api'

const NUTRIENT_COLS = [
  { key: 'calories',   label: 'Cal',    unit: 'kcal' },
  { key: 'protein',    label: 'Prot',   unit: 'g' },
  { key: 'carbs',      label: 'Carbs',  unit: 'g' },
  { key: 'fat',        label: 'Fat',    unit: 'g' },
  { key: 'fibre',      label: 'Fibre',  unit: 'g' },
  { key: 'iron',       label: 'Iron',   unit: 'mg' },
  { key: 'calcium',    label: 'Ca',     unit: 'mg' },
]

const SUGGESTIONS = [
  'Samosa', 'Bhel puri', 'Vada pav', 'Pani puri', 'Chakli',
  'Murukku', 'Sev', 'Chivda', 'Kachori', 'Dhokla',
  'Khakhra', 'Thepla', 'Misal pav', 'Dabeli', 'Pav bhaji',
  'Chole bhature', 'Aloo tikki', 'Dahi puri', 'Ragda pattice', 'Jalebi'
]

export default function DatasetGenPage() {
  const [input, setInput]       = useState('')
  const [tags, setTags]         = useState([])
  const [results, setResults]   = useState([])
  const [selected, setSelected] = useState(new Set())
  const [loading, setLoading]   = useState(false)
  const [saving, setSaving]     = useState(false)
  const [error, setError]       = useState('')
  const [saveMsg, setSaveMsg]   = useState('')

  const addTag = (name) => {
    const clean = name.trim()
    if (clean && !tags.includes(clean) && tags.length < 20) {
      setTags(t => [...t, clean])
    }
    setInput('')
  }

  const handleKeyDown = (e) => {
    if ((e.key === 'Enter' || e.key === ',') && input.trim()) {
      e.preventDefault()
      addTag(input)
    }
  }

  const removeTag = (tag) => setTags(t => t.filter(x => x !== tag))

  const generate = async () => {
    if (tags.length === 0) return
    setLoading(true); setError(''); setResults([]); setSaveMsg('')
    try {
      const { data } = await api.post('/dataset/generate', { foods: tags })
      setResults(data.results)
      // Auto-select all non-duplicate entries
      setSelected(new Set(
        data.results.filter(r => !r.already_in_db).map(r => r.name)
      ))
    } catch (e) {
      setError(e.response?.data?.error || 'Generation failed')
    } finally { setLoading(false) }
  }

  const toggleSelect = (name) => {
    setSelected(prev => {
      const next = new Set(prev)
      next.has(name) ? next.delete(name) : next.add(name)
      return next
    })
  }

  const toggleAll = () => {
    if (selected.size === results.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(results.map(r => r.name)))
    }
  }

  const saveSelected = async () => {
    const toSave = results.filter(r => selected.has(r.name))
    if (!toSave.length) return
    const flagged = toSave.filter(r => r.flagged)
    if (flagged.length > 0) {
      const names = flagged.map(f => f.name).join(', ')
      if (!window.confirm(`⚠️ ${flagged.length} food(s) have values that deviate >40% from category averages: ${names}.\n\nSave anyway?`)) return
    }
    setSaving(true); setSaveMsg(''); setError('')
    try {
      const { data } = await api.post('/dataset/save', { foods: toSave })
      setSaveMsg(`Saved ${data.saved_count} foods to database. ${data.skipped_count > 0 ? `(${data.skipped_count} already existed)` : ''}`)
      // Remove saved from results
      setResults(prev => prev.filter(r => !data.saved.includes(r.name)))
      setSelected(new Set())
    } catch (e) {
      setError(e.response?.data?.error || 'Save failed')
    } finally { setSaving(false) }
  }

  const exportCSV = () => {
    window.open('/api/dataset/export', '_blank')
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <AutoAwesomeIcon color="primary" />
        <Typography variant="h5" fontWeight={700}>AI Dataset Generator</Typography>
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Generate nutritional data for Indian foods not in IFCT 2017 using Groq LLaMA3.
        Review the estimates, then save approved entries to your database.
      </Typography>

      {/* Input */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>Enter Food Names</Typography>

          <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
            <TextField
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type a food name and press Enter..."
              size="small"
              sx={{ flex: 1 }}
              helperText="Press Enter or comma to add. Max 20 foods."
            />
            <Button variant="outlined" onClick={() => addTag(input)} disabled={!input.trim()}>
              Add
            </Button>
          </Box>

          {/* Tags */}
          {tags.length > 0 && (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75, mb: 2 }}>
              {tags.map(tag => (
                <Chip key={tag} label={tag} onDelete={() => removeTag(tag)}
                  color="primary" variant="outlined" size="small" />
              ))}
            </Box>
          )}

          {/* Suggestions */}
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
            Quick add popular Indian snacks:
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
            {SUGGESTIONS.filter(s => !tags.includes(s)).slice(0, 12).map(s => (
              <Chip key={s} label={s} size="small" onClick={() => addTag(s)}
                variant="outlined" sx={{ cursor: 'pointer' }} />
            ))}
          </Box>

          <Button
            variant="contained"
            startIcon={loading ? <CircularProgress size={18} color="inherit" /> : <AutoAwesomeIcon />}
            onClick={generate}
            disabled={tags.length === 0 || loading}
            size="large"
          >
            {loading ? `Generating for ${tags.length} foods...` : `Generate Nutrition Data`}
          </Button>
        </CardContent>
      </Card>

      {error   && <Alert severity="error"   sx={{ mb: 2 }}>{error}</Alert>}
      {saveMsg && <Alert severity="success" sx={{ mb: 2 }}>{saveMsg}</Alert>}

      {/* Results table */}
      {results.length > 0 && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, flexWrap: 'wrap', gap: 1 }}>
              <Typography variant="h6">
                Results — {results.length} foods
                <Typography component="span" variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                  ({selected.size} selected)
                </Typography>
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button variant="outlined" size="small" startIcon={<DownloadIcon />} onClick={exportCSV}>
                  Export Saved as CSV
                </Button>
                <Button
                  variant="contained"
                  size="small"
                  startIcon={saving ? <CircularProgress size={16} color="inherit" /> : <SaveIcon />}
                  onClick={saveSelected}
                  disabled={selected.size === 0 || saving}
                >
                  Save {selected.size} to Database
                </Button>
              </Box>
            </Box>

            <Box sx={{ overflowX: 'auto' }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell padding="checkbox">
                      <Checkbox
                        checked={selected.size === results.length && results.length > 0}
                        indeterminate={selected.size > 0 && selected.size < results.length}
                        onChange={toggleAll}
                        size="small"
                      />
                    </TableCell>
                    <TableCell><strong>Food Name</strong></TableCell>
                    <TableCell><strong>Group</strong></TableCell>
                    <TableCell><strong>Diet</strong></TableCell>
                    {NUTRIENT_COLS.map(c => (
                      <TableCell key={c.key} align="right">
                        <Tooltip title={`${c.label} per 100g (${c.unit})`}>
                          <strong>{c.label}</strong>
                        </Tooltip>
                      </TableCell>
                    ))}
                    <TableCell align="right"><strong>₹/100g</strong></TableCell>
                    <TableCell><strong>Status</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {results.map(row => (
                    <TableRow
                      key={row.name}
                      selected={selected.has(row.name)}
                      sx={{ opacity: row.already_in_db ? 0.5 : 1 }}
                    >
                      <TableCell padding="checkbox">
                        <Checkbox
                          checked={selected.has(row.name)}
                          onChange={() => toggleSelect(row.name)}
                          size="small"
                          disabled={row.already_in_db}
                        />
                      </TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>{row.name}</TableCell>
                      <TableCell>
                        <Typography variant="caption">{row.food_group}</Typography>
                      </TableCell>
                      <TableCell>
                        <Chip label={row.diet_type} size="small"
                          color={row.diet_type === 'veg' ? 'success' : 'error'}
                          variant="outlined" />
                      </TableCell>
                      {NUTRIENT_COLS.map(c => (
                        <TableCell key={c.key} align="right">
                          {Number(row[c.key]).toFixed(c.key === 'iron' || c.key === 'calcium' ? 1 : 1)}
                        </TableCell>
                      ))}
                      <TableCell align="right">₹{row.price_per_100g_inr}</TableCell>
                      <TableCell>
                        {row.flagged
                          ? <Chip label="⚠️ Review" size="small" color="error" />
                          : row.already_in_db
                          ? <Chip label="In DB" size="small" color="default" />
                          : <Chip label="New ✓" size="small" color="primary" variant="outlined" />}
                        {row.flagged && row.flags?.map((f, i) => (
                          <Tooltip key={i} title={`${f.macro}: AI=${f.ai_value}, avg=${f.category_avg} (${f.deviation_pct}% off)`} arrow>
                            <Typography variant="caption" color="error" sx={{ display: 'block', cursor: 'help' }}>
                              {f.macro} ±{f.deviation_pct}%
                            </Typography>
                          </Tooltip>
                        ))}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>

            <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
              ⚠️ Values are AI estimates based on typical Indian recipes. Not lab-verified.
              Good for general nutrition tracking but not clinical research.
            </Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  )
}
