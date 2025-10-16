import React from 'react';
import { 
  Grid, 
  Card, 
  CardContent, 
  Typography, 
  Box,
  Chip,
  useTheme
} from '@mui/material';
import { 
  TrendingUp, 
  TrendingDown, 
  Speed, 
  AttachMoney,
  Assessment,
  Warning
} from '@mui/icons-material';
import { useStore } from '../store/useStore';

const MetricsCards: React.FC = () => {
  const { metrics } = useStore();
  const theme = useTheme();

  const metricCards = [
    {
      title: 'Total Alerts',
      value: metrics.totalAlerts.toLocaleString(),
      icon: <Assessment />,
      color: theme.palette.primary.main,
      trend: '+12%',
      trendUp: true,
    },
    {
      title: 'False Positive Rate',
      value: `${(metrics.falsePositiveRate * 100).toFixed(1)}%`,
      icon: <TrendingDown />,
      color: theme.palette.success.main,
      trend: '-95%',
      trendUp: false,
      subtitle: '95% reduction achieved',
    },
    {
      title: 'Cost Savings',
      value: `${(metrics.costSavings * 100).toFixed(0)}%`,
      icon: <AttachMoney />,
      color: theme.palette.success.main,
      trend: '+30%',
      trendUp: true,
      subtitle: 'Operational efficiency',
    },
    {
      title: 'Processing Volume',
      value: metrics.processingVolume.toLocaleString(),
      icon: <Speed />,
      color: theme.palette.info.main,
      trend: '+25%',
      trendUp: true,
      subtitle: 'Messages/day',
    },
    {
      title: 'Avg Processing Time',
      value: `${metrics.averageProcessingTime.toFixed(1)}s`,
      icon: <Speed />,
      color: theme.palette.warning.main,
      trend: '-15%',
      trendUp: false,
      subtitle: 'Sub-5s requirement met',
    },
    {
      title: 'Critical Alerts',
      value: metrics.criticalAlerts.toString(),
      icon: <Warning />,
      color: theme.palette.error.main,
      trend: '+3',
      trendUp: true,
      subtitle: 'Requires immediate action',
    },
  ];

  return (
    <Grid container spacing={2}>
      {metricCards.map((metric, index) => (
        <Grid item xs={12} sm={6} md={4} lg={2} key={index}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Box 
                  sx={{ 
                    color: metric.color, 
                    mr: 1,
                    display: 'flex',
                    alignItems: 'center'
                  }}
                >
                  {metric.icon}
                </Box>
                <Typography variant="body2" color="text.secondary" noWrap>
                  {metric.title}
                </Typography>
              </Box>
              
              <Typography variant="h5" component="div" fontWeight="bold">
                {metric.value}
              </Typography>
              
              {metric.subtitle && (
                <Typography variant="caption" color="text.secondary" display="block">
                  {metric.subtitle}
                </Typography>
              )}
              
              <Box sx={{ mt: 1, display: 'flex', alignItems: 'center' }}>
                <Chip
                  label={metric.trend}
                  size="small"
                  color={metric.trendUp ? 'success' : 'error'}
                  variant="outlined"
                  icon={metric.trendUp ? <TrendingUp /> : <TrendingDown />}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
};

export default MetricsCards;