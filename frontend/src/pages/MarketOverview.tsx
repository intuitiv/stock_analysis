import React, { ReactElement } from 'react';
import { Box, Typography, Grid, Paper, CircularProgress, Alert } from '@mui/material';
import { useMarketData } from '../hooks/useMarketData';
import { MarketIndices, StockSummary, SectorPerformance } from '../utils/api';

interface IndexCardProps {
  index: MarketIndices;
}

interface MoverCardProps {
  mover: StockSummary;
  type: 'gainer' | 'loser';
}

interface SectorRowProps {
  sector: SectorPerformance;
}

const IndexCard: React.FC<IndexCardProps> = ({ index }): ReactElement => {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', my: 1 }}>
      <Typography>{index.name}</Typography>
      <Box>
        <Typography component="span" sx={{ mr: 2 }}>
          {index.price.toFixed(2)}
        </Typography>
        <Typography
          component="span"
          color={index.changePercent >= 0 ? 'success.main' : 'error.main'}
        >
          {index.changePercent >= 0 ? '+' : ''}
          {index.changePercent.toFixed(2)}%
        </Typography>
      </Box>
    </Box>
  );
};

const MoverCard: React.FC<MoverCardProps> = ({ mover, type }): ReactElement => {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', my: 1 }}>
      <Typography>{mover.name || mover.symbol}</Typography>
      <Typography
        color={type === 'gainer' ? 'success.main' : 'error.main'}
      >
        {type === 'gainer' ? '+' : ''}
        {mover.changePercent.toFixed(2)}%
      </Typography>
    </Box>
  );
};

const SectorRow: React.FC<SectorRowProps> = ({ sector }): ReactElement => {
  return (
    <Grid item xs={12} sm={6} md={4}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography>{sector.name}</Typography>
        <Typography
          color={sector.performance >= 0 ? 'success.main' : 'error.main'}
        >
          {sector.performance >= 0 ? '+' : ''}
          {sector.performance.toFixed(2)}%
        </Typography>
      </Box>
    </Grid>
  );
};

const MarketOverview: React.FC = (): ReactElement => {
  const { loading, error, data } = useMarketData();

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Market Overview
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Market Indices
            </Typography>
            {data?.indices.map((index) => (
              <IndexCard key={index.symbol} index={index} />
            ))}
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Top Movers
            </Typography>
            <Box>
              <Typography variant="subtitle2" color="success.main" gutterBottom>
                Top Gainers
              </Typography>
              {data?.gainers.slice(0, 5).map((gainer) => (
                <MoverCard key={gainer.symbol} mover={gainer} type="gainer" />
              ))}
            </Box>
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" color="error.main" gutterBottom>
                Top Losers
              </Typography>
              {data?.losers.slice(0, 5).map((loser) => (
                <MoverCard key={loser.symbol} mover={loser} type="loser" />
              ))}
            </Box>
          </Paper>
        </Grid>
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Sector Performance
            </Typography>
            <Grid container spacing={2}>
              {data?.sectors.map((sector) => (
                <SectorRow key={sector.name} sector={sector} />
              ))}
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default MarketOverview;
