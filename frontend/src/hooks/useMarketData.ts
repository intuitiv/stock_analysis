import { useState, useEffect } from 'react';
import { getMarketOverview, getSectorPerformance } from '../utils/api';

import { MarketOverviewData } from '../utils/api';

export const useMarketData = (): {
  loading: boolean;
  error: string | null;
  data: MarketOverviewData | null;
  refetch: () => Promise<void>;
} => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<MarketOverviewData | null>(null);

  const fetchData = async () => {
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
        gainers: overviewData.gainers || [],
        losers: overviewData.losers || [],
        sectors: sectorData || []
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch market data');
    } finally {
      setLoading(false);
    }
  };

  // Fetch data on component mount
  useEffect(() => {
    fetchData();
    
    // Optional: Set up polling for real-time updates
    const intervalId = setInterval(fetchData, 60000); // Refresh every minute
    
    return () => clearInterval(intervalId);
  }, []);

  return {
    loading,
    error,
    data,
    refetch: fetchData
  };
};
