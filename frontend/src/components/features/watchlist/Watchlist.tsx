import React from 'react';
import { Typography, List, ListItem, ListItemText, Paper } from '@mui/material';

// Mock data - replace with actual API/store data
const mockWatchlist = [
  { symbol: 'AAPL', name: 'Apple Inc.', price: 170.50, change: 2.5 },
  { symbol: 'MSFT', name: 'Microsoft Corp.', price: 285.30, change: -1.2 },
  { symbol: 'GOOGL', name: 'Alphabet Inc.', price: 2450.00, change: 1.8 }
];

const Watchlist: React.FC = (): React.ReactElement => {
  // TODO: Fetch watchlist data from API or state

  return (
    <Paper elevation={2} sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Watchlist
      </Typography>
      <List>
        {mockWatchlist.map((stock) => (
          <ListItem key={stock.symbol}>
            <ListItemText
              primary={
                <Typography variant="subtitle1">
                  {stock.symbol} - {stock.name}
                </Typography>
              }
              secondary={
                <Typography
                  component="span"
                  variant="body2"
                  color={stock.change >= 0 ? 'success.main' : 'error.main'}
                >
                  ${stock.price.toFixed(2)} ({stock.change > 0 ? '+' : ''}{stock.change}%)
                </Typography>
              }
            />
          </ListItem>
        ))}
      </List>
    </Paper>
  );
};

export default Watchlist;
