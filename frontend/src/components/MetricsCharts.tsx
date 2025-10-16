import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Grid,
  Box,
  useTheme,
} from '@mui/material';
import { PieChart } from '@mui/x-charts/PieChart';
import { BarChart } from '@mui/x-charts/BarChart';
import { useStore } from '../store/useStore';

const MetricsCharts: React.FC = () => {
  const { metrics } = useStore();
  const theme = useTheme();

  // Risk level distribution data
  const riskDistributionData = [
    { 
      id: 0, 
      value: metrics.criticalAlerts, 
      label: 'Critical',
      color: theme.palette.error.main,
    },
    { 
      id: 1, 
      value: metrics.highAlerts, 
      label: 'High',
      color: theme.palette.warning.main,
    },
    { 
      id: 2, 
      value: metrics.mediumAlerts, 
      label: 'Medium',
      color: theme.palette.info.main,
    },
    { 
      id: 3, 
      value: metrics.lowAlerts, 
      label: 'Low',
      color: theme.palette.success.main,
    },
  ];

  // Performance metrics data
  const performanceData = [
    {
      metric: 'False Positive Rate',
      current: metrics.falsePositiveRate * 100,
      target: 5,
      unit: '%',
    },
    {
      metric: 'Cost Savings',
      current: metrics.costSavings * 100,
      target: 30,
      unit: '%',
    },
    {
      metric: 'Avg Processing Time',
      current: metrics.averageProcessingTime,
      target: 5,
      unit: 's',
    },
  ];

  // Weekly trend data (mock data for demo)
  const weeklyTrendData = [
    { day: 'Mon', alerts: 35, processed: 180 },
    { day: 'Tue', alerts: 42, processed: 220 },
    { day: 'Wed', alerts: 28, processed: 195 },
    { day: 'Thu', alerts: 51, processed: 240 },
    { day: 'Fri', alerts: 38, processed: 210 },
    { day: 'Sat', alerts: 15, processed: 120 },
    { day: 'Sun', alerts: 12, processed: 95 },
  ];

  return (
    <Grid container spacing={2}>
      {/* Risk Level Distribution */}
      <Grid item xs={12} md={6}>
        <Card sx={{ height: '400px' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Alert Risk Distribution
            </Typography>
            <Box sx={{ height: '320px', display: 'flex', justifyContent: 'center' }}>
              <PieChart
                series={[
                  {
                    data: riskDistributionData,
                    highlightScope: { faded: 'global', highlighted: 'item' },
                    faded: { innerRadius: 30, additionalRadius: -30, color: 'gray' },
                  },
                ]}
                width={350}
                height={300}
              />
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Performance Metrics */}
      <Grid item xs={12} md={6}>
        <Card sx={{ height: '400px' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Performance vs Targets
            </Typography>
            <Box sx={{ height: '320px' }}>
              <BarChart
                xAxis={[{ 
                  scaleType: 'band', 
                  data: performanceData.map(d => d.metric),
                  tickLabelStyle: { fontSize: 12 },
                }]}
                series={[
                  {
                    data: performanceData.map(d => d.current),
                    label: 'Current',
                    color: theme.palette.primary.main,
                  },
                  {
                    data: performanceData.map(d => d.target),
                    label: 'Target',
                    color: theme.palette.grey[400],
                  },
                ]}
                width={350}
                height={300}
              />
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Weekly Trend */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Weekly Activity Trend
            </Typography>
            <Box sx={{ height: '300px' }}>
              <BarChart
                xAxis={[{ 
                  scaleType: 'band', 
                  data: weeklyTrendData.map(d => d.day),
                }]}
                series={[
                  {
                    data: weeklyTrendData.map(d => d.alerts),
                    label: 'Alerts Generated',
                    color: theme.palette.warning.main,
                  },
                  {
                    data: weeklyTrendData.map(d => d.processed),
                    label: 'Messages Processed',
                    color: theme.palette.primary.main,
                  },
                ]}
                width={800}
                height={280}
              />
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Business Impact Summary */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Business Impact Summary
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={4}>
                <Box sx={{ textAlign: 'center', p: 2 }}>
                  <Typography variant="h4" color="success.main" fontWeight="bold">
                    95%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Reduction in False Positives
                  </Typography>
                  <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                    From 50% to 5% false positive rate
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Box sx={{ textAlign: 'center', p: 2 }}>
                  <Typography variant="h4" color="primary.main" fontWeight="bold">
                    30%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Cost Savings Achieved
                  </Typography>
                  <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                    Reduced operational overhead
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Box sx={{ textAlign: 'center', p: 2 }}>
                  <Typography variant="h4" color="info.main" fontWeight="bold">
                    &lt;5s
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Average Processing Time
                  </Typography>
                  <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                    Real-time compliance analysis
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default MetricsCharts;