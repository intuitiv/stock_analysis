import React from 'react';
import { getMarketOverview, getSectorPerformance } from '../utils/api';

interface MarketOverviewData {
  indices: {
    symbol: string;
    name: string;
    price: number;
    change: number;
    changePercent: number;
  }[];
  topGainers: {
    symbol: string;
    name: string;
    changePercent: number;
  }[];
  topLosers: {
    symbol: string;
    name: string;
    changePercent: number;
  }[];
  sectors: {
    name: string;
    performance: number;
  }[];
}

export const useMarketData = (): {
  loading: boolean;
  error: string | null;
  data: MarketOverviewData | null;
  refetch: () => Promise<void>;
} => {
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [data, setData] = React.useState<MarketOverviewData | null>(null);

  const fetchData = React.useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch market overview and sector data in parallel
      const [overviewData, sectorData] = await Promise.all([
        getMarketOverview(),
        getSectorPerformance()
      ]);

      setData({
        indices: overviewData.indices || [],
        topGainers: overviewData.gainers || [],
        topLosers: overviewData.losers || [],
        sectors: sectorData || []
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch market data');
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch data on component mount
  React.useEffect(() => {
    fetchData();
    
    // Optional: Set up polling for real-time updates
    const intervalId = setInterval(fetchData, 60000); // Refresh every minute
    
    return () => clearInterval(intervalId);
  }, [fetchData]);

  return {
    loading,
    error,
    data,
    refetch: fetchData
  };
};