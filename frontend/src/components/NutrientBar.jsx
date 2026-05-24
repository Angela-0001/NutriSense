import React from 'react'
import { Box, Typography, LinearProgress, Tooltip } from '@mui/material'

/**
 * Shows a nutrient name, intake vs RDA, and a colour-coded progress bar.
 * pct > 100 → green, 50-100 → orange, < 50 → red
 */
export default function NutrientBar({ label, value, rda, unit }) {
  const pct = rda > 0 ? Math.min((value / rda) * 100, 150) : 0
  const color = pct >= 100 ? 'success' : pct >= 50 ? 'warning' : 'error'

  return (
    <Box sx={{ mb: 1.5 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
        <Typography variant="body2" fontWeight={500}>{label}</Typography>
        <Tooltip title={`RDA: ${rda}${unit}`}>
          <Typography variant="body2" color="text.secondary">
            {value?.toFixed(1)}{unit} / {rda}{unit}
          </Typography>
        </Tooltip>
      </Box>
      <LinearProgress
        variant="determinate"
        value={Math.min(pct, 100)}
        color={color}
        sx={{ height: 8, borderRadius: 4 }}
      />
    </Box>
  )
}
