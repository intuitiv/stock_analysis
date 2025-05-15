import React from 'react';
import { useParams } from 'react-router-dom';
import { Box, Typography, Grid, Paper } from '@mui/material';

const StockAnalysis = () => {
  const { symbol } = useParams();

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Stock Analysis: {symbol || 'Select a Stock'}
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Price Chart
            </Typography>
            <Typography>
              Coming soon: Interactive price chart
            </Typography>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Technical Analysis
            </Typography>
            <Typography>
              Coming soon: Technical indicators and patterns
            </Typography>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Fundamental Analysis
            </Typography>
            <Typography>
              Coming soon: Key financial metrics and ratios
            </Typography>
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Company News
            </Typography>
            <Typography>
              Coming soon: Latest news and updates about {symbol || 'the company'}
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default StockAnalysis;
