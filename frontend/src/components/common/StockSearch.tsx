import React, { useState, useEffect } from 'react';
import TextField from '@mui/material/TextField';
import Autocomplete from '@mui/material/Autocomplete';
import CircularProgress from '@mui/material/CircularProgress';
import Box from '@mui/material/Box';
// import { searchStocks } from '../../utils/api'; // Example API call

interface StockOption {
  symbol: string;
  name: string;
}

interface StockSearchProps {
  onStockSelect: (symbol: string | null) => void;
  label?: string;
  initialValue?: StockOption | null;
}

const StockSearch: React.FC<StockSearchProps> = ({ 
  onStockSelect, 
  label = "Search Stock",
  initialValue = null 
}) => {
  const [open, setOpen] = useState(false);
  const [options, setOptions] = useState<readonly StockOption[]>([]);
  const [loading, setLoading] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [value, setValue] = useState<StockOption | null>(initialValue);

  useEffect(() => {
    let active = true;

    if (inputValue === '' || inputValue.length < 1) { // Start searching after 1 char
      setOptions(value ? [value] : []);
      setLoading(false);
      return undefined;
    }

    setLoading(true);
    // --- TODO: Replace with actual API call ---
    const fetchOptions = async () => {
      console.log(`Searching for: ${inputValue}`);
      // const results = await searchStocks(inputValue); // Assume API call
      // Dummy results based on input
      let dummyResults: StockOption[] = [];
       if (inputValue.toLowerCase().includes('aapl')) dummyResults.push({ symbol: 'AAPL', name: 'Apple Inc.' });
       if (inputValue.toLowerCase().includes('goog')) dummyResults.push({ symbol: 'GOOGL', name: 'Alphabet Inc. (Class A)' });
       if (inputValue.toLowerCase().includes('msft')) dummyResults.push({ symbol: 'MSFT', name: 'Microsoft Corporation' });
       if (inputValue.toLowerCase().includes('tsla')) dummyResults.push({ symbol: 'TSLA', name: 'Tesla, Inc.' });
       
      await new Promise(resolve => setTimeout(resolve, 500)); // Simulate network delay

      if (active) {
        let newOptions: readonly StockOption[] = [];
        if (value) {
          newOptions = [value];
        }
        if (dummyResults) {
          // Filter out duplicates if value is already in results
          newOptions = [...newOptions, ...dummyResults.filter(opt => opt.symbol !== value?.symbol)];
        }
        setOptions(newOptions);
      }
      setLoading(false);
    };

    fetchOptions();
    // --- End of TODO section ---

    return () => {
      active = false;
    };
  }, [value, inputValue]); // Depend on value and inputValue

  return (
    <Autocomplete
      sx={{ width: 300 }}
      open={open}
      onOpen={() => setOpen(true)}
      onClose={() => setOpen(false)}
      isOptionEqualToValue={(option, val) => option.symbol === val.symbol}
      getOptionLabel={(option) => `${option.symbol} - ${option.name}`}
      options={options}
      loading={loading}
      value={value}
      onInputChange={(event, newInputValue) => {
        setInputValue(newInputValue);
      }}
      onChange={(event, newValue) => {
        setOptions(newValue ? [newValue, ...options.filter(opt => opt.symbol !== newValue.symbol)] : options);
        setValue(newValue);
        onStockSelect(newValue ? newValue.symbol : null); // Call callback
      }}
      renderInput={(params) => (
        <TextField
          {...params}
          label={label}
          InputProps={{
            ...params.InputProps,
            endAdornment: (
              <React.Fragment>
                {loading ? <CircularProgress color="inherit" size={20} /> : null}
                {params.InputProps.endAdornment}
              </React.Fragment>
            ),
          }}
        />
      )}
      renderOption={(props, option) => (
         <Box component="li" {...props} key={option.symbol}>
           {option.symbol} - {option.name}
         </Box>
       )}
    />
  );
}

export default StockSearch;
