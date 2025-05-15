import React from 'react';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';

const Dashboard: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <Typography>
        Welcome to the NAETRA Dashboard. Your personalized market overview will appear here.
      </Typography>
      {/* Add Dashboard components here */}
    </Box>
  );
};

export default Dashboard;
