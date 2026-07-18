# Placeholder for SEC EDGAR data fetching service
from __future__ import annotations

import requests
import time
from app.core.config import settings

USER_AGENT = settings.SEC_EDGAR_USER_AGENT
COMPANY_FACTS_URL = settings.SEC_COMPANY_FACTS_URL # Requires CIK
SUBMISSIONS_URL = settings.SEC_SUBMISSIONS_URL # Requires CIK padded to 10 digits
RATE_LIMIT_DELAY = 1.0 / settings.SEC_RATE_LIMIT_PER_SEC # Delay between requests

def _get_headers():
    """Returns headers required for SEC EDGAR API requests."""
    if not USER_AGENT:
        raise ValueError("SEC_EDGAR_USER_AGENT must be set in config.")
    return {'User-Agent': USER_AGENT}

def _make_sec_request(url: str) -> dict:
    """Makes a request to SEC EDGAR API with rate limiting."""
    try:
        time.sleep(RATE_LIMIT_DELAY)
        response = requests.get(url, headers=_get_headers())
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from SEC EDGAR ({url}): {e}")
        return {}
    except ValueError as e: # Handle missing User-Agent
        print(e)
        return {}
    except Exception as e:
        print(f"An unexpected error occurred during SEC request: {e}")
        return {}

def get_company_cik(symbol: str) -> str | None:
    """
    Placeholder: Looks up the CIK for a given stock symbol.
    This usually requires a mapping service or another API call.
    A common source is: https://www.sec.gov/files/company_tickers.json
    """
    # TODO: Implement CIK lookup logic
    # Example: Fetch the mapping file, cache it, and search
    print(f"CIK lookup for {symbol} not implemented yet.")
    # Example CIK for Apple Inc.
    if symbol.upper() == "AAPL":
        return "320193" 
    return None

def get_company_facts(cik: str) -> dict:
    """Fetches company facts (financials) using CIK."""
    if not cik:
        return {}
    url = f"{COMPANY_FACTS_URL}CIK{cik}.json"
    return _make_sec_request(url)

def get_company_submissions(cik: str) -> dict:
    """Fetches company submission history using CIK (padded)."""
    if not cik:
        return {}
    # CIK must be zero-padded to 10 digits for the submissions API
    padded_cik = cik.zfill(10)
    url = f"{SUBMISSIONS_URL}CIK{padded_cik}.json"
    return _make_sec_request(url)

def get_latest_filings(symbol: str, filing_type: str = "10-K") -> list:
    """Fetches latest filings of a specific type for a symbol."""
    cik = get_company_cik(symbol)
    if not cik:
        return []
        
    submissions = get_company_submissions(cik)
    if not submissions or 'filings' not in submissions or 'recent' not in submissions['filings']:
        return []

    recent_filings = submissions['filings']['recent']
    results = []

    # Iterate through the filings and construct the desired information
    # Assuming all lists in recent_filings (like 'form', 'accessionNumber', etc.) are of the same length
    # and correspond to each other by index.
    
    # Get the number of filings based on one of the lists, e.g., 'form'
    num_filings = len(recent_filings.get('form', []))

    for i in range(num_filings):
        try:
            form = recent_filings.get('form', [])[i]
            if form == filing_type:
                filing_info = {
                    "accessionNumber": recent_filings.get('accessionNumber', [])[i],
                    "filingDate": recent_filings.get('filingDate', [])[i],
                    "reportDate": recent_filings.get('reportDate', [])[i],
                    "form": form,
                    "primaryDocument": recent_filings.get('primaryDocument', [])[i],
                    # Add more fields as needed from recent_filings, ensuring keys exist
                    # Example: "size": recent_filings.get('size', [])[i] if 'size' in recent_filings else None
                }
                # Check for required fields before appending
                if all(key in filing_info and filing_info[key] is not None for key in ["accessionNumber", "filingDate", "form", "primaryDocument"]):
                    results.append(filing_info)
                else:
                    print(f"Skipping filing {i} for CIK {cik} due to missing essential data.")

        except IndexError:
            # This handles cases where lists might be jagged, though SEC API should be consistent
            print(f"Index error processing filing {i} for CIK {cik}. Lists might be of different lengths.")
            continue 
        except KeyError as e:
            # This handles cases where an expected key (like 'accessionNumber') is missing from recent_filings dict
            print(f"Key error processing filing {i} for CIK {cik}: Missing key {e}")
            continue

    # TODO: Add logic to fetch the actual filing document content if needed
    return results

# Add functions to parse specific filing types (e.g., parse_10k)

# Placeholder class definition to satisfy linters if they expect this module to provide it.
# This class is not actively used as its import is commented out in market_data_service.py.
from app.services.market_data.interface import MarketDataProvider
from typing import List, Dict, Any, Optional
from datetime import datetime

class SECEdgarProvider(MarketDataProvider):
    """
    Placeholder provider for SEC EDGAR data.
    The actual SEC EDGAR logic is currently implemented as standalone functions in this module.
    This class structure is provided for consistency with other data providers if a class-based
    approach is adopted for SEC EDGAR in the future.
    """
    async def get_price_data(self, symbol: str, start_date: datetime, end_date: datetime, interval: str = "1d") -> List[Dict[str, Any]]:
        # SEC EDGAR primarily provides filings, not direct price data.
        # This method would need to be implemented if price data sourcing from SEC (e.g., via forms) is required.
        print(f"SECEdgarProvider.get_price_data for {symbol} not implemented.")
        return []

    async def get_current_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        print(f"SECEdgarProvider.get_current_quote for {symbol} not implemented.")
        return None

    async def get_company_profile(self, symbol: str) -> Optional[Dict[str, Any]]:
        # Could potentially use get_company_facts or submissions here
        cik = get_company_cik(symbol)
        if cik:
            # Example: return basic info from submissions if needed
            # submissions = get_company_submissions(cik)
            # return {"cik": cik, "name": submissions.get("name")}
            print(f"SECEdgarProvider.get_company_profile for {symbol} (CIK: {cik}) - using function-based approach for now.")
            # This is just a placeholder; actual implementation would call the module-level functions.
            return {"symbol": symbol, "cik": cik, "name": "Name from SEC (placeholder)"}
        return None

    async def get_financial_statements(self, symbol: str, statement_type: str, period: str = "annual", limit: int = 5) -> List[Dict[str, Any]]:
        cik = get_company_cik(symbol)
        if cik:
            # This would typically parse data from get_company_facts or specific filings
            print(f"SECEdgarProvider.get_financial_statements for {symbol} (CIK: {cik}) - using function-based approach for now.")
            # facts = get_company_facts(cik) # Example call
            return [{"date": "YYYY-MM-DD", "metric": "value"}] # Placeholder
        return []

    async def get_key_financial_ratios(self, symbol: str) -> Optional[Dict[str, Any]]:
        print(f"SECEdgarProvider.get_key_financial_ratios for {symbol} not implemented.")
        return None

    async def get_market_news(self, symbols: Optional[List[str]] = None, topics: Optional[List[str]] = None, limit: int = 20) -> List[Dict[str, Any]]:
        # SEC EDGAR is for filings, not general market news.
        # Could return latest filings as a form of "news" for a company.
        if symbols and symbols[0]:
             return get_latest_filings(symbols[0], limit=limit) # type: ignore
        print(f"SECEdgarProvider.get_market_news not implemented for general queries.")
        return []

    async def search_symbols(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        # Could implement a CIK lookup based on query string
        print(f"SECEdgarProvider.search_symbols for '{query}' not implemented robustly.")
        # Basic CIK lookup attempt
        cik = get_company_cik(query) 
        if cik:
            return [{"symbol": query.upper(), "name": f"Company with CIK {cik} (Name TBD)", "cik": cik}]
        return []
