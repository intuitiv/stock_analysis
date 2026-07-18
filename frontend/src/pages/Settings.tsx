import React from 'react';
import { Box, Typography, Grid, Paper, Switch, FormGroup, FormControlLabel } from '@mui/material';

const Settings = () => {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Display Settings
            </Typography>
            <FormGroup>
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Dark Mode"
              />
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Real-time Updates"
              />
              <FormControlLabel
                control={<Switch />}
                label="Desktop Notifications"
              />
            </FormGroup>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Trading Preferences
            </Typography>
            <FormGroup>
              <FormControlLabel
                control={<Switch />}
                label="Enable Trading"
              />
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Price Alerts"
              />
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Portfolio Updates"
              />
            </FormGroup>
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Data Sources
            </Typography>
            <FormGroup>
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Use Real-time Market Data"
              />
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Enable Technical Analysis"
              />
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Enable Fundamental Analysis"
              />
            </FormGroup>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Settings;
