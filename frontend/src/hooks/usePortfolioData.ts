import * as React from 'react';
import { getPortfolios, getPortfolioById } from '../utils/api';
import { Portfolio, PortfolioListData } from '../types/portfolio';

const { useState, useEffect, useCallback } = React;

export const usePortfolioData = (portfolioId?: string) => {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [portfolios, setPortfolios] = useState<PortfolioListData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPortfolio = useCallback(async (id: string) => {
    try {
      setLoading(true);
      const numericId = parseInt(id, 10);
      if (isNaN(numericId)) {
        throw new Error('Invalid portfolio ID');
      }
      const data = await getPortfolioById(numericId);
      setPortfolio(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch portfolio data');
      setPortfolio(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchPortfolios = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getPortfolios();
      setPortfolios(data || []); // Assuming getPortfolios returns an array
      setError(null);
      // If a specific portfolioId isn't requested, and portfolios are found,
      // fetch the first one by default.
      if (!portfolioId && data && data.length > 0) {
        fetchPortfolio(data[0].id.toString());
      } else if (portfolioId) {
         fetchPortfolio(portfolioId);
      } else {
        setLoading(false); // No portfolios and no specific ID
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch portfolios list');
      setPortfolios([]);
      setLoading(false);
    }
  }, [portfolioId, fetchPortfolio]);

  useEffect(() => {
    if (portfolioId) {
      fetchPortfolio(portfolioId);
    } else {
      // Fetch all portfolios to potentially load the default/first one
      fetchPortfolios();
    }
  }, [portfolioId, fetchPortfolio, fetchPortfolios]);

  return { 
    portfolio, 
    portfolios, 
    loading, 
    error, 
    refreshPortfolio: fetchPortfolio, 
    refreshPortfolios: fetchPortfolios 
  };
};
