import React from 'react';
import { Typography, List, ListItem, ListItemText } from '@mui/material';

// TODO: Replace with actual API types
type NewsItem = {
  id: string;
  title: string;
  summary: string;
  date: string;
  source: string;
};

// Mock data - replace with actual API call
const mockNews: NewsItem[] = [
  {
    id: '1',
    title: 'Market Update: Stocks Rally on Economic Data',
    summary: 'Major indices surge as economic indicators show strong growth...',
    date: '2024-03-15',
    source: 'Financial Times'
  },
  {
    id: '2',
    title: 'Fed Announces Interest Rate Decision',
    summary: 'Federal Reserve maintains current interest rates, signals future adjustments...',
    date: '2024-03-14',
    source: 'Reuters'
  }
];

const MarketNews: React.FC = (): React.ReactElement => {
  // TODO: Fetch market news data from API (e.g., /market/news or /stocks/{symbol}/news for general market)
  // For now, using mock data.
  return (
    <div>
      <Typography variant="h6" gutterBottom>
        Market News
      </Typography>
      <List>
        {mockNews.map((item) => (
          <ListItem key={item.id}>
            <ListItemText
              primary={item.title}
              secondary={
                <>
                  <Typography
                    component="span"
                    variant="body2"
                    color="textPrimary"
                  >
                    {item.source} - {item.date}
                  </Typography>
                  <br />
                  {item.summary}
                </>
              }
            />
          </ListItem>
        ))}
      </List>
    </div>
  );
};

export default MarketNews;
