import React from 'react';
import { Grid, Box, Typography } from '@mui/material';
import { useQuery } from 'react-query';
import { apiService } from '../services/api';
import { useStore } from '../store/useStore';
import MetricsCards from './MetricsCards';
import AlertsTable from './AlertsTable';
import AlertFilters from './AlertFilters';
import MetricsCharts from './MetricsCharts';

const Dashboard: React.FC = () => {
  const { setAlerts, setMetrics, setLoading, setError } = useStore();

  // Real-time alerts query
  const { isLoading: alertsLoading, error: alertsError } = useQuery(
    'alerts',
    apiService.getAlerts,
    {
      onSuccess: (data) => {
        setAlerts(data);
        setError(null);
      },
      onError: (error: Error) => {
        setError(error.message);
      },
    }
  );

  // Metrics query
  const { isLoading: metricsLoading, error: metricsError } = useQuery(
    'metrics',
    apiService.getMetrics,
    {
      onSuccess: (data) => {
        setMetrics(data);
      },
      onError: (error: Error) => {
        console.error('Failed to load metrics:', error);
      },
    }
  );

  React.useEffect(() => {
    setLoading(alertsLoading || metricsLoading);
  }, [alertsLoading, metricsLoading, setLoading]);

  if (alertsError || metricsError) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h6" color="error">
          Error loading dashboard data
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          {alertsError?.message || metricsError?.message}
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Compliance Dashboard
      </Typography>
      
      <Grid container spacing={3}>
        {/* Metrics Overview */}
        <Grid item xs={12}>
          <MetricsCards />
        </Grid>

        {/* Charts */}
        <Grid item xs={12} lg={8}>
          <MetricsCharts />
        </Grid>

        {/* Alert Filters */}
        <Grid item xs={12} lg={4}>
          <AlertFilters />
        </Grid>

        {/* Alerts Table */}
        <Grid item xs={12}>
          <AlertsTable />
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;