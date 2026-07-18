import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import { formatNumber, formatCurrency } from '../../../utils/formatters'; // Assuming formatters exist

interface FinancialsTableProps {
  symbol: string;
  fundamentalData: any; // Replace 'any' with a proper type for fundamental results
}

const FinancialsTable: React.FC<FinancialsTableProps> = ({ symbol, fundamentalData }) => {
  // TODO: Implement table rendering for financial data (P/E, EPS, Revenue, etc.)
  const overview = fundamentalData?.overview || {};
  const financials = fundamentalData?.financials || {};

  const rows = [
    { name: 'Market Cap', value: formatCurrency(overview.market_cap) },
    { name: 'P/E Ratio', value: formatNumber(overview.pe_ratio) },
    { name: 'P/B Ratio', value: formatNumber(overview.pb_ratio) },
    { name: 'Dividend Yield', value: `${formatNumber(overview.dividend_yield * 100)}%` },
    { name: 'EPS', value: formatNumber(overview.eps) },
    { name: 'Beta', value: formatNumber(overview.beta) },
    { name: 'Sector', value: overview.sector },
    { name: 'Industry', value: overview.industry },
    { name: 'Latest Revenue', value: formatCurrency(financials.total_revenue) },
    { name: 'Latest Net Income', value: formatCurrency(financials.net_income) },
  ];

  return (
    <Box sx={{ mt: 2 }}>
      <Typography variant="h6">Fundamental Data for {symbol}</Typography>
      {fundamentalData?.overview?.error ? (
         <Typography color="error" sx={{mt: 1}}>{fundamentalData.overview.error}</Typography>
      ) : (
        <TableContainer component={Paper} sx={{ mt: 1 }}>
          <Table size="small" aria-label="fundamental data table">
            <TableHead>
              <TableRow>
                <TableCell>Metric</TableCell>
                <TableCell align="right">Value</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.map((row) => (
                <TableRow key={row.name}>
                  <TableCell component="th" scope="row">
                    {row.name}
                  </TableCell>
                  <TableCell align="right">{row.value || 'N/A'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
};

export default FinancialsTable;
