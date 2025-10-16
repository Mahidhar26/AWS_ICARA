import React, { useState, useMemo } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TableSortLabel,
  Chip,
  IconButton,
  Collapse,
  Box,
  Menu,
  MenuItem,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  KeyboardArrowDown,
  KeyboardArrowUp,
  MoreVert,
} from '@mui/icons-material';
import { useStore, Alert } from '../store/useStore';
import { apiService } from '../services/api';

type Order = 'asc' | 'desc';
type OrderBy = keyof Alert;

interface AlertRowProps {
  alert: Alert;
  onStatusChange: (alertId: string, status: Alert['status']) => void;
}

const AlertRow: React.FC<AlertRowProps> = ({ alert, onStatusChange }) => {
  const [open, setOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const theme = useTheme();

  const getRiskColor = (riskLevel: Alert['riskLevel']) => {
    switch (riskLevel) {
      case 'CRITICAL': return theme.palette.error.main;
      case 'HIGH': return theme.palette.warning.main;
      case 'MEDIUM': return theme.palette.info.main;
      case 'LOW': return theme.palette.success.main;
      default: return theme.palette.grey[500];
    }
  };

  const getStatusColor = (status: Alert['status']) => {
    switch (status) {
      case 'OPEN': return 'error';
      case 'INVESTIGATING': return 'warning';
      case 'RESOLVED': return 'success';
      case 'FALSE_POSITIVE': return 'default';
      default: return 'default';
    }
  };

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleStatusChange = (newStatus: Alert['status']) => {
    onStatusChange(alert.id, newStatus);
    handleMenuClose();
  };

  return (
    <>
      <TableRow sx={{ '& > *': { borderBottom: 'unset' } }}>
        <TableCell>
          <IconButton
            aria-label="expand row"
            size="small"
            onClick={() => setOpen(!open)}
          >
            {open ? <KeyboardArrowUp /> : <KeyboardArrowDown />}
          </IconButton>
        </TableCell>
        <TableCell>
          <Chip
            label={alert.riskLevel}
            size="small"
            sx={{
              backgroundColor: getRiskColor(alert.riskLevel),
              color: 'white',
              fontWeight: 'bold',
            }}
          />
        </TableCell>
        <TableCell>
          <Chip
            label={alert.type}
            size="small"
            variant="outlined"
          />
        </TableCell>
        <TableCell>
          <Typography variant="body2" fontWeight="medium">
            {alert.title}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {alert.description}
          </Typography>
        </TableCell>
        <TableCell>
          {(alert.confidence * 100).toFixed(0)}%
        </TableCell>
        <TableCell>
          {new Date(alert.timestamp).toLocaleString()}
        </TableCell>
        <TableCell>
          <Chip
            label={alert.status}
            size="small"
            color={getStatusColor(alert.status) as any}
            variant="outlined"
          />
        </TableCell>
        <TableCell>
          <IconButton onClick={handleMenuClick}>
            <MoreVert />
          </IconButton>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
          >
            <MenuItem onClick={() => handleStatusChange('INVESTIGATING')}>
              Mark as Investigating
            </MenuItem>
            <MenuItem onClick={() => handleStatusChange('RESOLVED')}>
              Mark as Resolved
            </MenuItem>
            <MenuItem onClick={() => handleStatusChange('FALSE_POSITIVE')}>
              Mark as False Positive
            </MenuItem>
            <MenuItem onClick={() => handleStatusChange('OPEN')}>
              Reopen
            </MenuItem>
          </Menu>
        </TableCell>
      </TableRow>
      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={8}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Box sx={{ margin: 1 }}>
              <Typography variant="h6" gutterBottom component="div">
                Violation Details
              </Typography>
              {alert.violations && alert.violations.length > 0 ? (
                alert.violations.map((violation, index) => (
                  <Box key={index} sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" color="primary">
                      {violation.type} - {violation.regulation}
                    </Typography>
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      {violation.explanation}
                    </Typography>
                  </Box>
                ))
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No specific violations detected.
                </Typography>
              )}
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
};

const AlertsTable: React.FC = () => {
  const { alerts, filters, updateAlertStatus } = useStore();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [order, setOrder] = useState<Order>('desc');
  const [orderBy, setOrderBy] = useState<OrderBy>('timestamp');
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const handleRequestSort = (property: OrderBy) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleStatusChange = async (alertId: string, status: Alert['status']) => {
    updateAlertStatus(alertId, status);
    await apiService.updateAlertStatus(alertId, status);
  };

  const filteredAndSortedAlerts = useMemo(() => {
    let filtered = alerts.filter(alert => {
      if (filters.riskLevel.length > 0 && !filters.riskLevel.includes(alert.riskLevel)) {
        return false;
      }
      if (filters.type.length > 0 && !filters.type.includes(alert.type)) {
        return false;
      }
      if (filters.status.length > 0 && !filters.status.includes(alert.status)) {
        return false;
      }
      return true;
    });

    filtered.sort((a, b) => {
      let aValue: any = a[orderBy];
      let bValue: any = b[orderBy];

      if (orderBy === 'timestamp') {
        aValue = new Date(aValue as string).getTime();
        bValue = new Date(bValue as string).getTime();
      }

      if (aValue === undefined || bValue === undefined) {
        return 0;
      }

      if (order === 'asc') {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      } else {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
      }
    });

    return filtered;
  }, [alerts, filters, order, orderBy]);

  const paginatedAlerts = filteredAndSortedAlerts.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  if (isMobile) {
    // Mobile-friendly card layout
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Recent Alerts ({filteredAndSortedAlerts.length})
          </Typography>
          {paginatedAlerts.map((alert) => (
            <Card key={alert.id} variant="outlined" sx={{ mb: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Chip
                    label={alert.riskLevel}
                    size="small"
                    color={alert.riskLevel === 'CRITICAL' ? 'error' : 
                           alert.riskLevel === 'HIGH' ? 'warning' : 'default'}
                  />
                  <Typography variant="caption" color="text.secondary">
                    {new Date(alert.timestamp).toLocaleDateString()}
                  </Typography>
                </Box>
                <Typography variant="subtitle2" gutterBottom>
                  {alert.title}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {alert.description}
                </Typography>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Chip
                    label={alert.status}
                    size="small"
                    variant="outlined"
                  />
                  <Typography variant="caption">
                    {(alert.confidence * 100).toFixed(0)}% confidence
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          ))}
          <TablePagination
            component="div"
            count={filteredAndSortedAlerts.length}
            page={page}
            onPageChange={handleChangePage}
            rowsPerPage={rowsPerPage}
            onRowsPerPageChange={handleChangeRowsPerPage}
            rowsPerPageOptions={[5, 10, 25]}
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Recent Alerts ({filteredAndSortedAlerts.length})
        </Typography>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell />
                <TableCell>
                  <TableSortLabel
                    active={orderBy === 'riskLevel'}
                    direction={orderBy === 'riskLevel' ? order : 'asc'}
                    onClick={() => handleRequestSort('riskLevel')}
                  >
                    Risk Level
                  </TableSortLabel>
                </TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Alert</TableCell>
                <TableCell>
                  <TableSortLabel
                    active={orderBy === 'confidence'}
                    direction={orderBy === 'confidence' ? order : 'asc'}
                    onClick={() => handleRequestSort('confidence')}
                  >
                    Confidence
                  </TableSortLabel>
                </TableCell>
                <TableCell>
                  <TableSortLabel
                    active={orderBy === 'timestamp'}
                    direction={orderBy === 'timestamp' ? order : 'asc'}
                    onClick={() => handleRequestSort('timestamp')}
                  >
                    Timestamp
                  </TableSortLabel>
                </TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {paginatedAlerts.map((alert) => (
                <AlertRow
                  key={alert.id}
                  alert={alert}
                  onStatusChange={handleStatusChange}
                />
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          component="div"
          count={filteredAndSortedAlerts.length}
          page={page}
          onPageChange={handleChangePage}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          rowsPerPageOptions={[5, 10, 25, 50]}
        />
      </CardContent>
    </Card>
  );
};

export default AlertsTable;