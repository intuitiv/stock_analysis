import React from 'react';
import { getPortfolios, getPortfolioById } from '../utils/api';
import { Portfolio, PortfolioListData } from '../types/portfolio';

export const usePortfolioData = (portfolioId?: string) => {
  const [portfolio, setPortfolio] = React.useState<Portfolio | null>(null);
  const [portfolios, setPortfolios] = React.useState<PortfolioListData[]>([]);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<string | null>(null);

  const fetchPortfolio = React.useCallback(async (id: string) => {
    try {
      setLoading(true);
      const data = await getPortfolioById(id);
      setPortfolio(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch portfolio data');
      setPortfolio(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchPortfolios = React.useCallback(async () => {
    try {
      setLoading(true);
      const data = await getPortfolios();
      setPortfolios(data || []); // Assuming getPortfolios returns an array
      setError(null);
      // If a specific portfolioId isn't requested, and portfolios are found,
      // fetch the first one by default.
      if (!portfolioId && data && data.length > 0) {
        fetchPortfolio(data[0].id);
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

  React.useEffect(() => {
    if (portfolioId) {
      fetchPortfolio(portfolioId);
    } else {
      // Fetch all portfolios to potentially load the default/first one
      fetchPortfolios();
    }
  }, [portfolioId, fetchPortfolio, fetchPortfolios]);

  return { portfolio, portfolios, loading, error, refreshPortfolio: fetchPortfolio, refreshPortfolios: fetchPortfolios };
};