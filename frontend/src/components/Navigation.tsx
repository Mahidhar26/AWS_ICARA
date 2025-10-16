import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  Box, 
  Tabs, 
  Tab, 
  useTheme, 
  useMediaQuery 
} from '@mui/material';
import { 
  Dashboard as DashboardIcon, 
  Search as SearchIcon 
} from '@mui/icons-material';

const Navigation: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const currentTab = location.pathname === '/analyzer' ? 1 : 0;

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    if (newValue === 0) {
      navigate('/');
    } else if (newValue === 1) {
      navigate('/analyzer');
    }
  };

  return (
    <Box sx={{ borderBottom: 1, borderColor: 'divider', bgcolor: 'background.paper' }}>
      <Tabs 
        value={currentTab} 
        onChange={handleTabChange}
        variant={isMobile ? 'fullWidth' : 'standard'}
        sx={{ px: 2 }}
      >
        <Tab 
          icon={<DashboardIcon />} 
          label={isMobile ? 'Dashboard' : 'Alert Dashboard'} 
          iconPosition="start"
        />
        <Tab 
          icon={<SearchIcon />} 
          label={isMobile ? 'Analyzer' : 'Compliance Analyzer'} 
          iconPosition="start"
        />
      </Tabs>
    </Box>
  );
};

export default Navigation;