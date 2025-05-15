import React from 'react';
import { Grid, Paper } from '@mui/material';
import PortfolioOverview from '../components/features/portfolio/PortfolioOverview';
import Watchlist from '../components/features/watchlist/Watchlist';
import MarketNews from '../components/features/market/MarketNews';

const Dashboard: React.FC = (): React.ReactElement => {
  return (
    <Grid container spacing={3}>
      {/* Portfolio Overview Section */}
      <Grid item xs={12} lg={8}>
        <Paper elevation={2} sx={{ p: 2 }}>
          <PortfolioOverview />
        </Paper>
      </Grid>

      {/* Watchlist Section */}
      <Grid item xs={12} sm={6} lg={4}>
        <Watchlist />
      </Grid>

      {/* Market News Section */}
      <Grid item xs={12} sm={6} lg={4}>
        <MarketNews />
      </Grid>
    </Grid>
  );
};

export default Dashboard;
