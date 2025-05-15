import React from 'react';
import { Box, Typography, Card, CardContent, Grid, CircularProgress, Alert } from '@mui/material';
import { formatCurrency, formatPercentage } from '../../../utils/formatters';
import { usePortfolioData } from '../../../hooks/usePortfolioData';

const PortfolioOverview: React.FC<{ portfolioId?: string }> = ({ portfolioId }): React.ReactElement => {
  const { portfolio, loading, error } = usePortfolioData(portfolioId);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" p={3}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">Error loading portfolio: {error}</Alert>
    );
  }

  if (!portfolio) {
    return (
      <Alert severity="info">No portfolio data available.</Alert>
    );
  }

  const {
    name,
    total_value = 0,
    total_gain_loss_value = 0,
    total_gain_loss_percent = 0,
    day_change_value = 0,
    day_change_percent = 0,
    positions = []
  } = portfolio;

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        {name}
      </Typography>

      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Value
              </Typography>
              <Typography variant="h4">
                {formatCurrency(total_value)}
              </Typography>
              <Typography color={total_gain_loss_value >= 0 ? 'success.main' : 'error.main'}>
                {formatCurrency(total_gain_loss_value, true)} ({formatPercentage(total_gain_loss_percent)})
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Today's Change
              </Typography>
              <Typography variant="h4" color={day_change_value >= 0 ? 'success.main' : 'error.main'}>
                {formatCurrency(day_change_value, true)}
              </Typography>
              <Typography color={day_change_value >= 0 ? 'success.main' : 'error.main'}>
                {formatPercentage(day_change_percent)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Typography variant="h6" gutterBottom>
        Positions ({positions.length})
      </Typography>

      <Grid container spacing={2}>
        {positions.map((position) => (
          <Grid item xs={12} sm={6} md={4} key={position.id}>
            <Card>
              <CardContent>
                <Typography variant="h6">{position.symbol}</Typography>
                <Typography color="textSecondary">
                  {position.quantity} shares @ {formatCurrency(position.purchase_price)}
                </Typography>
                <Typography>
                  Current Value: {formatCurrency(position.value)}
                </Typography>
                {position.gain_loss != null && (
                  <Typography color={position.gain_loss >= 0 ? 'success.main' : 'error.main'}>
                    {formatCurrency(position.gain_loss, true)} ({formatPercentage(position.gain_loss_percent)})
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default PortfolioOverview;
