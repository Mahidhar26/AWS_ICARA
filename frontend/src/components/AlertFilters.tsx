import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Box,
  OutlinedInput,
  Button,
} from '@mui/material';
import { SelectChangeEvent } from '@mui/material/Select';
import { Clear as ClearIcon } from '@mui/icons-material';
import { useStore } from '../store/useStore';

const ITEM_HEIGHT = 48;
const ITEM_PADDING_TOP = 8;
const MenuProps = {
  PaperProps: {
    style: {
      maxHeight: ITEM_HEIGHT * 4.5 + ITEM_PADDING_TOP,
      width: 250,
    },
  },
};

const AlertFilters: React.FC = () => {
  const { filters, updateFilters } = useStore();

  const handleRiskLevelChange = (event: SelectChangeEvent<string[]>) => {
    const value = event.target.value;
    updateFilters({
      riskLevel: typeof value === 'string' ? value.split(',') : value,
    });
  };

  const handleTypeChange = (event: SelectChangeEvent<string[]>) => {
    const value = event.target.value;
    updateFilters({
      type: typeof value === 'string' ? value.split(',') : value,
    });
  };

  const handleStatusChange = (event: SelectChangeEvent<string[]>) => {
    const value = event.target.value;
    updateFilters({
      status: typeof value === 'string' ? value.split(',') : value,
    });
  };

  const clearAllFilters = () => {
    updateFilters({
      riskLevel: [],
      type: [],
      status: [],
      dateRange: [null, null],
    });
  };

  const hasActiveFilters = 
    filters.riskLevel.length > 0 || 
    filters.type.length > 0 || 
    filters.status.length > 0;

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">
            Filters
          </Typography>
          {hasActiveFilters && (
            <Button
              size="small"
              startIcon={<ClearIcon />}
              onClick={clearAllFilters}
            >
              Clear All
            </Button>
          )}
        </Box>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <FormControl fullWidth size="small">
            <InputLabel>Risk Level</InputLabel>
            <Select
              multiple
              value={filters.riskLevel}
              onChange={handleRiskLevelChange}
              input={<OutlinedInput label="Risk Level" />}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((value) => (
                    <Chip 
                      key={value} 
                      label={value} 
                      size="small"
                      color={
                        value === 'CRITICAL' ? 'error' :
                        value === 'HIGH' ? 'warning' :
                        value === 'MEDIUM' ? 'info' : 'success'
                      }
                    />
                  ))}
                </Box>
              )}
              MenuProps={MenuProps}
            >
              <MenuItem value="CRITICAL">Critical</MenuItem>
              <MenuItem value="HIGH">High</MenuItem>
              <MenuItem value="MEDIUM">Medium</MenuItem>
              <MenuItem value="LOW">Low</MenuItem>
            </Select>
          </FormControl>

          <FormControl fullWidth size="small">
            <InputLabel>Alert Type</InputLabel>
            <Select
              multiple
              value={filters.type}
              onChange={handleTypeChange}
              input={<OutlinedInput label="Alert Type" />}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((value) => (
                    <Chip key={value} label={value} size="small" variant="outlined" />
                  ))}
                </Box>
              )}
              MenuProps={MenuProps}
            >
              <MenuItem value="COMMUNICATION">Communication</MenuItem>
              <MenuItem value="TRANSACTION">Transaction</MenuItem>
            </Select>
          </FormControl>

          <FormControl fullWidth size="small">
            <InputLabel>Status</InputLabel>
            <Select
              multiple
              value={filters.status}
              onChange={handleStatusChange}
              input={<OutlinedInput label="Status" />}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((value) => (
                    <Chip 
                      key={value} 
                      label={value} 
                      size="small" 
                      variant="outlined"
                      color={
                        value === 'OPEN' ? 'error' :
                        value === 'INVESTIGATING' ? 'warning' :
                        value === 'RESOLVED' ? 'success' : 'default'
                      }
                    />
                  ))}
                </Box>
              )}
              MenuProps={MenuProps}
            >
              <MenuItem value="OPEN">Open</MenuItem>
              <MenuItem value="INVESTIGATING">Investigating</MenuItem>
              <MenuItem value="RESOLVED">Resolved</MenuItem>
              <MenuItem value="FALSE_POSITIVE">False Positive</MenuItem>
            </Select>
          </FormControl>
        </Box>

        {hasActiveFilters && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Active filters applied
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default AlertFilters;