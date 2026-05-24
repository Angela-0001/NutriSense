import React, { useEffect, useState, useCallback, useRef } from 'react'
import {
  Box, Grid, Card, CardContent, Typography, TextField, Button,
  MenuItem, Autocomplete, IconButton, Chip, CircularProgress,
  Table, TableBody, TableCell, TableHead, TableRow, Alert,
  Tooltip, Dialog, DialogTitle, DialogContent, DialogActions,
  LinearProgress
} from '@mui/material'
import DeleteIcon       from '@mui/icons-material/Delete'
import AddIcon          from '@mui/icons-material/Add'
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'
import PhotoCameraIcon  from '@mui/icons-material/PhotoCamera'
import CheckCircleIcon  from '@mui/icons-material/CheckCircle'
import api from '../api/api'

const MEAL_TYPES = ['breakfast', 'lunch', 'dinner', 'snack']
const TODAY = new Date().toISOString().split('T')[0]

const SERVING_PRESETS = {
  cereals: [
    { label: '1 cup cooked',   grams: 180, description: '~1 standard bowl of cooked rice/upma' },
    { label: '½ cup cooked',   grams: 90,  description: 'Small serving' },
    { label: '1 roti/chapati', grams: 35,  description: '1 medium wheat roti (~6 inch)' },
    { label: '2 rotis',        grams: 70,  description: '2 medium rotis' },
    { label: '1 paratha',      grams: 80,  description: '1 stuffed paratha' },
    { label: '1 idli',         grams: 40,  description: '1 standard idli' },
    { label: '2 idlis',        grams: 80,  description: '2 standard idlis' },
    { label: '1 dosa',         grams: 75,  description: '1 plain dosa' },
    { label: '100g',           grams: 100, description: 'Standard 100g' },
  ],
  pulses: [
    { label: '1 katori dal',  grams: 150, description: '1 small bowl of cooked dal (~150g)' },
    { label: '½ katori dal',  grams: 75,  description: 'Half bowl of cooked dal' },
    { label: '1 cup cooked',  grams: 180, description: '1 cup cooked legumes (rajma, chana)' },
    { label: '100g',          grams: 100, description: 'Standard 100g' },
  ],
  vegetables: [
    { label: '1 katori sabzi', grams: 100, description: '1 small bowl of cooked vegetable' },
    { label: '½ katori',       grams: 50,  description: 'Half bowl' },
    { label: '1 medium piece', grams: 80,  description: '1 medium-sized vegetable (tomato, carrot)' },
    { label: '1 cup raw',      grams: 60,  description: '1 cup loosely packed raw greens' },
    { label: '100g',           grams: 100, description: 'Standard 100g' },
  ],
  fruits: [
    { label: '1 small fruit',  grams: 80,  description: '1 small apple/orange/banana' },
    { label: '1 medium fruit', grams: 130, description: '1 medium apple/orange' },
    { label: '1 banana',       grams: 100, description: '1 medium banana (peeled)' },
    { label: '1 cup pieces',   grams: 150, description: '1 cup cut fruit' },
    { label: '100g',           grams: 100, description: 'Standard 100g' },
  ],
  'milk and milk products': [
    { label: '1 glass milk',   grams: 200, description: '1 standard glass (~200ml)' },
    { label: '½ glass milk',   grams: 100, description: 'Half glass' },
    { label: '1 katori curd',  grams: 150, description: '1 small bowl of curd/yogurt' },
    { label: '1 slice paneer', grams: 40,  description: '1 slice paneer (~40g)' },
    { label: '100g',           grams: 100, description: 'Standard 100g' },
  ],
  'meat, poultry and fish': [
    { label: '1 small piece',  grams: 80,  description: '1 small piece of meat/fish' },
    { label: '1 medium piece', grams: 120, description: '1 medium piece' },
    { label: '1 egg',          grams: 55,  description: '1 whole egg' },
    { label: '2 eggs',         grams: 110, description: '2 whole eggs' },
    { label: '100g',           grams: 100, description: 'Standard 100g' },
  ],
  'nuts and oilseeds': [
    { label: '1 small handful', grams: 20, description: '~20g, about 15-20 nuts' },
    { label: '1 tbsp seeds',    grams: 10, description: '1 tablespoon seeds (til, flax)' },
    { label: '2 tbsp',          grams: 20, description: '2 tablespoons' },
    { label: '100g',            grams: 100, description: 'Standard 100g' },
  ],
  'fats and oils': [
    { label: '1 tsp oil',  grams: 5,   description: '1 teaspoon cooking oil' },
    { label: '1 tbsp oil', grams: 14,  description: '1 tablespoon cooking oil' },
    { label: '100g',       grams: 100, description: 'Standard 100g' },
  ],
  'sugar and jaggery': [
    { label: '1 tsp sugar',   grams: 5,   description: '1 teaspoon sugar' },
    { label: '1 tbsp sugar',  grams: 12,  description: '1 tablespoon sugar' },
    { label: '1 small piece', grams: 15,  description: '1 small piece of jaggery' },
    { label: '100g',          grams: 100, description: 'Standard 100g' },
  ],
  'snacks and sweets': [
    { label: '1 piece',        grams: 85,  description: '1 medium piece (samosa, kachori, vada)' },
    { label: '2 pieces',       grams: 170, description: '2 medium pieces' },
    { label: '1 small piece',  grams: 40,  description: '1 small piece (ladoo, barfi, peda)' },
    { label: '2 small pieces', grams: 80,  description: '2 small pieces' },
    { label: '1 plate',        grams: 150, description: '1 plate (bhel puri, chaat)' },
    { label: '1 cup',          grams: 100, description: '1 cup dry snack (chivda, sev, chakli)' },
    { label: '1 handful',      grams: 30,  description: '1 handful dry snack' },
    { label: '100g',           grams: 100, description: 'Standard 100g' },
  ],
  dishes: [
    { label: '1 plate',   grams: 300, description: '1 full plate (rice, biryani, pulao)' },
    { label: '1 katori',  grams: 150, description: '1 small bowl (dal, sabzi, curry)' },
    { label: '½ plate',   grams: 150, description: 'Half plate' },
    { label: '1 piece',   grams: 100, description: '1 piece (paratha, dosa, uttapam)' },
    { label: '100g',      grams: 100, description: 'Standard 100g' },
  ],
  default: [
    { label: '½ cup',  grams: 80,  description: 'Half cup serving' },
    { label: '1 cup',  grams: 160, description: '1 cup serving' },
    { label: '1 bowl', grams: 150, description: '1 standard bowl' },
    { label: '1 plate',grams: 250, description: '1 full plate' },
    { label: '100g',   grams: 100, description: 'Standard 100g' },
    { label: '150g',   grams: 150, description: '150g serving' },
    { label: '200g',   grams: 200, description: '200g serving' },
  ],
}

function getPresets(foodGroup) {
  if (!foodGroup) return SERVING_PRESETS.default
  const key = foodGroup.toLowerCase()
  return SERVING_PRESETS[key] || SERVING_PRESETS.default
}

const LIQUID_FOODS = ['milk', 'lassi', 'chai', 'tea', 'juice', 'water',
  'buttermilk', 'coconut water', 'coffee', 'beverage', 'drink', 'sherbet']

function isLiquid(foodName) {
  if (!foodName) return false
  return LIQUID_FOODS.some(l => foodName.toLowerCase().includes(l))
}

function gramsToHousehold(grams, foodName) {
  if (isLiquid(foodName || '')) {
    if (grams >= 180) return `${Math.round(grams / 200 * 10) / 10} glass (${grams}ml)`
    if (grams >= 80)  return `½ glass (${grams}ml)`
    return `${grams}ml`
  }
  const all = Object.values(SERVING_PRESETS).flat()
  const match = all.find(p => p.grams === grams)
  if (match && !match.label.endsWith('g')) return match.label
  return `${grams}g`
}

function NutritionPreview({ food, grams }) {
  if (!food || !grams) return null
  const f = grams / 100
  const displayQty = isLiquid(food.name) ? `${grams}ml` : gramsToHousehold(grams, food.name)
  return (
    <Box sx={{ mt: 1.5, p: 1.5, bgcolor: 'action.hover', borderRadius: 2 }}>
      <Typography variant="caption" fontWeight={700} color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
        Nutrition for {displayQty} of {food.name}:
      </Typography>
      <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
        {[
          ['Calories', (food.calories * f).toFixed(0), 'kcal', 'primary'],
          ['Protein',  (food.protein  * f).toFixed(1), 'g',    'info'],
          ['Iron',     (food.iron     * f).toFixed(2), 'mg',   'error'],
          ['Calcium',  (food.calcium  * f).toFixed(0), 'mg',   'warning'],
          ['Fibre',    (food.fibre    * f).toFixed(1), 'g',    'success'],
        ].map(([label, val, unit, color]) => (
          <Chip key={label} size="small" color={color} variant="outlined" label={`${label}: ${val}${unit}`} />
        ))}
      </Box>
    </Box>
  )
}

function SmartQuantityInput({ food, quantity, onQuantityChange }) {
  const [text, setText]         = useState('')
  const [loading, setLoading]   = useState(false)
  const [hint, setHint]         = useState('')
  const [activePreset, setActivePreset] = useState(null) // label of selected preset

  // When quantity changes externally (preset chips), update hint
  useEffect(() => {
    const all = Object.values(SERVING_PRESETS).flat()
    const match = all.find(p => p.grams === quantity)
    if (match && !match.label.endsWith('g')) {
      setHint(`${match.label} = ${quantity}g`)
      setActivePreset(match.label)
      setText(match.label)
    } else {
      setHint(`${quantity}g`)
      setActivePreset(null)
    }
  }, [quantity])

  const convert = async (val) => {
    const trimmed = val.trim()
    if (!trimmed) return

    // Plain number → treat as grams directly
    if (/^\d+(\.\d+)?$/.test(trimmed)) {
      onQuantityChange(Number(trimmed))
      setHint(`${trimmed}g`)
      setActivePreset(null)
      return
    }

    // Natural language → call Gemini
    if (!food) return
    setLoading(true)
    try {
      const { data } = await api.post('/unit/convert', {
        food_name: food.name,
        quantity_text: trimmed
      })
      onQuantityChange(Math.round(data.grams))
      setHint(`${trimmed} = ${Math.round(data.grams)}g`)
      setActivePreset(null)
    } catch (e) {
      setHint('Could not convert — enter grams directly')
    } finally { setLoading(false) }
  }

  const handleClear = () => {
    setText('')
    setHint('')
    setActivePreset(null)
  }

  return (
    <Box>
      <TextField
        label="Quantity"
        value={text}
        onChange={e => {
          setText(e.target.value)
          setActivePreset(null) // deselect preset as soon as user types
        }}
        onBlur={e => { if (e.target.value.trim()) convert(e.target.value) }}
        onKeyDown={e => { if (e.key === 'Enter' && text.trim()) convert(text) }}
        fullWidth
        size="small"
        placeholder="2 rotis, 1 katori…"
        InputProps={{
          endAdornment: loading
            ? <CircularProgress size={14} />
            : text
              ? <IconButton size="small" onClick={handleClear} sx={{ p: 0.3 }}>
                  <span style={{ fontSize: 14, lineHeight: 1 }}>×</span>
                </IconButton>
              : null
        }}
      />
      {hint && (
        <Typography
          variant="caption"
          color={hint.includes('=') ? 'primary.main' : 'text.secondary'}
          sx={{ display: 'block', mt: 0.3, fontWeight: hint.includes('=') ? 600 : 400 }}
        >
          {loading ? 'Estimating…' : hint}
        </Typography>
      )}
    </Box>
  )
}

export default function FoodLogPage() {
  const [date, setDate]         = useState(TODAY)
  const [logs, setLogs]         = useState([])
  const [daily, setDaily]       = useState(null)
  const [foods, setFoods]       = useState([])
  const [search, setSearch]     = useState('')
  const [selected, setSelected] = useState(null)
  const [mealType, setMealType] = useState('lunch')
  const [quantity, setQuantity] = useState(100)
  const [adding, setAdding]     = useState(false)
  const [error, setError]       = useState('')
  const [generating, setGenerating] = useState(false)
  const [visionOpen, setVisionOpen]       = useState(false)
  const [visionImage, setVisionImage]     = useState(null)
  const [visionPreview, setVisionPreview] = useState(null)
  const [visionLoading, setVisionLoading] = useState(false)
  const [visionResult, setVisionResult]   = useState(null)
  const [visionError, setVisionError]     = useState('')
  const fileInputRef = useRef(null)

  const presets = selected ? getPresets(selected.food_group) : SERVING_PRESETS.default

  const fetchLogs = useCallback(() => {
    api.get(`/logs/?date=${date}`).then(r => setLogs(r.data))
    api.get(`/logs/daily?date=${date}`).then(r => setDaily(r.data))
  }, [date])

  useEffect(() => { fetchLogs() }, [fetchLogs])

  useEffect(() => {
    if (search.length < 2) return
    const t = setTimeout(() => {
      api.get(`/foods/?q=${encodeURIComponent(search)}&limit=20`).then(r => setFoods(r.data))
    }, 300)
    return () => clearTimeout(t)
  }, [search])

  useEffect(() => {
    if (selected) setQuantity(getPresets(selected.food_group)[0].grams)
  }, [selected])

  const handleVisionImageChange = (e) => {
    const file = e.target.files[0]
    if (!file) return
    if (visionPreview) URL.revokeObjectURL(visionPreview)
    setVisionImage(file); setVisionPreview(URL.createObjectURL(file))
    setVisionResult(null); setVisionError(''); e.target.value = ''
  }

  const handleVisionEstimate = async () => {
    if (!visionImage || !selected) return
    setVisionLoading(true); setVisionError('')
    try {
      const form = new FormData()
      form.append('image', visionImage); form.append('food_name', selected.name)
      const { data } = await api.post('/vision/estimate-portion', form, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      setVisionResult(data)
    } catch (e) { setVisionError(e.response?.data?.error || 'Estimation failed.') }
    finally { setVisionLoading(false) }
  }

  const handleVisionApply = () => {
    if (visionResult) {
      setQuantity(visionResult.estimated_grams)
      setVisionOpen(false); setVisionImage(null); setVisionPreview(null); setVisionResult(null)
    }
  }

  const handleVisionClose = () => {
    setVisionOpen(false)
    if (visionPreview) URL.revokeObjectURL(visionPreview)
    setVisionImage(null); setVisionPreview(null); setVisionResult(null); setVisionError('')
  }

  const handleGenerateFood = async () => {
    if (!search.trim()) return
    setGenerating(true); setError('')
    try {
      const { data } = await api.post('/foods/generate-missing', { food_name: search.trim() })
      // Add to options and auto-select
      setFoods([data])
      setSelected(data)
    } catch (e) {
      setError(e.response?.data?.error || 'Could not generate food data')
    } finally { setGenerating(false) }
  }

  const handleAdd = async () => {
    if (!selected) return
    setAdding(true); setError('')
    try {
      const res = await api.post('/logs/', { food_id: selected.id, date, meal_type: mealType, quantity_grams: quantity })
      setSelected(null); setSearch(''); setQuantity(100); fetchLogs()
    } catch (e) { setError(e.response?.data?.error || 'Failed to add') }
    finally { setAdding(false) }
  }

  const handleDelete = async (id) => {
    await api.delete(`/logs/${id}`); fetchLogs()
  }

  const grouped = MEAL_TYPES.reduce((acc, m) => {
    acc[m] = logs.filter(l => l.meal_type === m); return acc
  }, {})

  return (
    <Box>
      <Typography variant="h5" fontWeight={700} sx={{ mb: 3 }}>Food Log</Typography>
      <TextField type="date" label="Date" value={date} onChange={e => setDate(e.target.value)}
        InputLabelProps={{ shrink: true }} sx={{ mb: 3 }} />

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>Add Food</Typography>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <Grid container spacing={2} alignItems="flex-start">
            <Grid item xs={12} sm={5}>
              <Autocomplete
                options={foods} getOptionLabel={o => o.name}
                isOptionEqualToValue={(o, v) => o.id === v.id}
                value={selected}
                onInputChange={(_, v) => setSearch(v)}
                onChange={(_, v) => { setSelected(v); setSearch(v?.name || '') }}
                renderOption={(props, o) => (
                  <Box component="li" {...props}>
                    <Box>
                      <Typography variant="body2">{o.name}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {o.food_group} · {o.calories} kcal/100g · ₹{o.price_per_100g_inr}/100g
                      </Typography>
                    </Box>
                  </Box>
                )}
                renderInput={params => <TextField {...params} label="Search food" fullWidth />}
                noOptionsText={
                  search.length < 2 ? 'Type at least 2 characters...' : (
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        "{search}" not found in database
                      </Typography>
                      <Button
                        size="small"
                        variant="outlined"
                        color="secondary"
                        disabled={generating}
                        onClick={handleGenerateFood}
                        startIcon={generating ? <CircularProgress size={14} /> : null}
                        sx={{ whiteSpace: 'nowrap', fontSize: 12 }}
                      >
                        {generating ? 'Generating…' : '✨ Add with AI'}
                      </Button>
                    </Box>
                  )
                }
              />
            </Grid>
            <Grid item xs={6} sm={2}>
              <TextField select label="Meal" value={mealType} onChange={e => setMealType(e.target.value)} fullWidth>
                {MEAL_TYPES.map(m => <MenuItem key={m} value={m} sx={{ textTransform: 'capitalize' }}>{m}</MenuItem>)}
              </TextField>
            </Grid>
            <Grid item xs={6} sm={2}>
              <SmartQuantityInput food={selected} quantity={quantity} onQuantityChange={setQuantity} />
            </Grid>
            <Grid item xs="auto">
              {/* Grams display — read-only, calculated from quantity */}
              <Box sx={{ pt: 0.5 }}>
                <Typography variant="caption" color="text.secondary" display="block">Grams</Typography>
                <Typography variant="h6" fontWeight={700} color="primary.main">
                  {quantity}g
                </Typography>
                <Typography variant="caption" color="text.secondary">calculated</Typography>
              </Box>
            </Grid>
            <Grid item xs="auto">
              <Tooltip title={selected ? 'Estimate from photo' : 'Select a food first'}>
                <span>
                  <IconButton color="primary" disabled={!selected} onClick={() => setVisionOpen(true)}
                    sx={{ mt: 0.5, border: '1px solid', borderColor: selected ? 'primary.main' : 'divider', borderRadius: 2 }}>
                    <PhotoCameraIcon />
                  </IconButton>
                </span>
              </Tooltip>
            </Grid>
            <Grid item xs={12} sm={3}>
              <Button variant="contained"
                startIcon={adding ? <CircularProgress size={16} color="inherit" /> : <AddIcon />}
                onClick={handleAdd} disabled={!selected || adding} fullWidth sx={{ height: 56 }}>
                Add to Log
              </Button>
            </Grid>
          </Grid>

          <Box sx={{ mt: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
              <Typography variant="body2" fontWeight={600}>
                {selected ? `Serving sizes for ${selected.food_group || 'this food'}:` : 'Common serving sizes:'}
              </Typography>
              <Tooltip title="Click a serving size to set quantity. Hover for description.">
                <InfoOutlinedIcon sx={{ fontSize: 16, color: 'text.secondary', cursor: 'help' }} />
              </Tooltip>
            </Box>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
              {presets.map(preset => (
                <Tooltip key={preset.label} title={`${preset.description} — click to select, click again to deselect`} arrow placement="top">
                  <Chip
                    label={`${preset.label} · ${preset.grams}g`}
                    onClick={() => {
                      // Toggle: clicking active preset deselects it
                      if (quantity === preset.grams) {
                        setQuantity(0)
                      } else {
                        setQuantity(preset.grams)
                      }
                    }}
                    variant={quantity === preset.grams ? 'filled' : 'outlined'}
                    color={quantity === preset.grams ? 'primary' : 'default'}
                    size="small"
                    sx={{ cursor: 'pointer', fontWeight: quantity === preset.grams ? 700 : 400 }}
                  />
                </Tooltip>
              ))}
            </Box>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
              {selected
                ? 'Click a size to fill quantity, or type your own above (e.g. "3 pieces", "half plate")'
                : '↑ Select a food above — serving sizes will update to match that food\'s category.'}
            </Typography>
            <NutritionPreview food={selected} grams={quantity} />
          </Box>
        </CardContent>
      </Card>

      {daily && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 1 }}>Daily Total</Typography>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              {[['Calories', daily.calories, 'kcal'], ['Protein', daily.protein, 'g'],
                ['Iron', daily.iron, 'mg'], ['Calcium', daily.calcium, 'mg'], ['Fibre', daily.fibre, 'g']
              ].map(([label, val, unit]) => (
                <Box key={label} sx={{ textAlign: 'center', minWidth: 80 }}>
                  <Typography variant="h6" fontWeight={700}>{val?.toFixed(1)}</Typography>
                  <Typography variant="caption" color="text.secondary">{label} ({unit})</Typography>
                </Box>
              ))}
            </Box>
          </CardContent>
        </Card>
      )}

      {MEAL_TYPES.map(meal => grouped[meal].length > 0 && (
        <Card key={meal} sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 1, textTransform: 'capitalize' }}>
              {{ breakfast: '🌅', lunch: '☀️', dinner: '🌙', snack: '🍎' }[meal]} {meal}
            </Typography>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Food</TableCell>
                  <TableCell align="right">Quantity</TableCell>
                  <TableCell align="right">Grams</TableCell>
                  <TableCell align="right">Calories</TableCell>
                  <TableCell align="right">Protein</TableCell>
                  <TableCell align="right">Iron</TableCell>
                  <TableCell />
                </TableRow>
              </TableHead>
              <TableBody>
                {grouped[meal].map(log => (
                  <TableRow key={log.id}>
                    <TableCell>
                      <Typography variant="body2">{log.food_name}</Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title={`${log.quantity_grams}g`} arrow>
                        <span style={{ cursor: 'help', borderBottom: '1px dashed #aaa' }}>
                          {gramsToHousehold(log.quantity_grams, log.food_name)}
                        </span>
                      </Tooltip>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" color="text.secondary">{log.quantity_grams}g</Typography>
                    </TableCell>
                    <TableCell align="right">{log.nutrition?.calories?.toFixed(0)}</TableCell>
                    <TableCell align="right">{log.nutrition?.protein?.toFixed(1)}g</TableCell>
                    <TableCell align="right">{log.nutrition?.iron?.toFixed(2)}mg</TableCell>
                    <TableCell align="right">
                      <IconButton size="small" color="error" onClick={() => handleDelete(log.id)}>
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ))}

      {logs.length === 0 && (
        <Typography color="text.secondary" sx={{ textAlign: 'center', mt: 4 }}>
          No food logged for this date.
        </Typography>
      )}

      <input ref={fileInputRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={handleVisionImageChange} />
      <Dialog open={visionOpen} onClose={handleVisionClose} maxWidth="sm" fullWidth>
        <DialogTitle>
          📷 Estimate Portion from Photo
          {selected && <Typography variant="body2" color="text.secondary">Food: <strong>{selected.name}</strong></Typography>}
        </DialogTitle>
        <DialogContent>
          {!visionPreview ? (
            <Box>
              <Box onClick={() => fileInputRef.current?.click()}
                sx={{ border: '2px dashed', borderColor: 'primary.main', borderRadius: 3,
                  p: 4, textAlign: 'center', cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' } }}>
                <PhotoCameraIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
                <Typography fontWeight={600}>Click to upload a photo</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>JPG, PNG, WEBP · Max 10MB</Typography>
                <Typography variant="caption" color="text.secondary">Tip: include a bowl or plate for better accuracy</Typography>
              </Box>
              <Button variant="outlined" fullWidth sx={{ mt: 1.5 }} onClick={() => fileInputRef.current?.click()}>Browse Files</Button>
            </Box>
          ) : (
            <Box>
              <Box component="img" src={visionPreview} alt="Food portion"
                sx={{ width: '100%', maxHeight: 400, objectFit: 'contain', borderRadius: 2, mb: 2, display: 'block' }} />
              <Button size="small" onClick={() => fileInputRef.current?.click()} sx={{ mb: 2 }}>Change photo</Button>
            </Box>
          )}
          {visionError && <Alert severity="error" sx={{ mt: 2 }}>{visionError}</Alert>}
          {visionLoading && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>Analysing portion size...</Typography>
              <LinearProgress />
            </Box>
          )}
          {visionResult && !visionLoading && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'action.hover', borderRadius: 2, border: '1px solid', borderColor: 'success.light' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <CheckCircleIcon color="success" />
                <Typography fontWeight={700} color="success.dark">Portion Estimated</Typography>
                <Chip label={`${visionResult.confidence} confidence`} size="small"
                  color={visionResult.confidence === 'high' ? 'success' : visionResult.confidence === 'medium' ? 'warning' : 'error'} />
              </Box>
              <Typography variant="h4" fontWeight={700} color="success.dark">{visionResult.estimated_grams}g</Typography>
              <Typography variant="body2" color="text.secondary">Range: {visionResult.range_min}g – {visionResult.range_max}g</Typography>
              {visionResult.reasoning && (
                <Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic' }}>"{visionResult.reasoning}"</Typography>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={handleVisionClose}>Cancel</Button>
          {visionPreview && !visionResult && (
            <Button variant="outlined" onClick={handleVisionEstimate} disabled={visionLoading}>
              {visionLoading ? <CircularProgress size={18} /> : 'Estimate Grams'}
            </Button>
          )}
          {visionResult && (
            <Button variant="contained" onClick={handleVisionApply} startIcon={<CheckCircleIcon />}>
              Use {visionResult.estimated_grams}g
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  )
}
