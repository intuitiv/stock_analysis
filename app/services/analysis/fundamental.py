from datetime import datetime
from typing import Dict, Any, Optional, List
import asyncio

from app.services.market_data_service import MarketDataService # Manages data providers
from app.core.config import settings
# from app.chaetra.llm import LLMManager # Optional: For summarizing or interpreting fundamental data

class FundamentalAnalyzer:
    def __init__(
        self, 
        market_data_service: MarketDataService
        # llm_manager: Optional[LLMManager] = None # Optional LLM for advanced analysis
    ):
        self.market_data_service = market_data_service
        # self.llm_manager = llm_manager

    async def get_company_overview(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetches and returns a company's profile and key overview metrics.
        """
        profile = await self.market_data_service.get_company_profile(symbol)
        ratios = await self.market_data_service.get_key_financial_ratios(symbol)

        if not profile and not ratios:
            return None
        
        overview = {**(profile or {}), **(ratios or {})}
        
        # Basic derived metrics or summaries can be added here
        # Example: Debt-to-Equity interpretation (if data available)
        # if overview.get('debt_to_equity') is not None:
        #     if overview['debt_to_equity'] > 1.5:
        #         overview['debt_level_assessment'] = 'High'
        #     elif overview['debt_to_equity'] < 0.5:
        #         overview['debt_level_assessment'] = 'Low'
        #     else:
        #         overview['debt_level_assessment'] = 'Moderate'
                
        return overview

    async def analyze_financial_statements(
        self, 
        symbol: str, 
        statement_types: Optional[List[str]] = None, # e.g., ["income_statement", "balance_sheet"]
        period: str = "annual", 
        limit: int = 3 # Number of past periods
    ) -> Dict[str, Any]:
        """
        Fetches and analyzes financial statements, calculating key growth rates and trends.
        """
        if statement_types is None:
            statement_types = ["income_statement", "balance_sheet", "cash_flow"]

        results = {"symbol": symbol, "period": period, "statements": {}}
        analysis_summary = {}

        for stmt_type in statement_types:
            statements_data = await self.market_data_service.get_financial_statements(
                symbol, stmt_type, period, limit
            )
            results["statements"][stmt_type] = statements_data
            
            # Perform basic trend analysis on key items (e.g., revenue, net income growth)
            # This is a simplified example. More sophisticated trend analysis would be needed.
            if statements_data and len(statements_data) > 1:
                key_metrics_trends = self._calculate_statement_trends(statements_data, stmt_type)
                analysis_summary[f"{stmt_type}_trends"] = key_metrics_trends
        
        results["analysis_summary"] = analysis_summary
        
        # Optional: Use LLM to summarize the financial health based on statements and trends
        # if self.llm_manager:
        #     summary_prompt = f"Summarize the financial health of {symbol} based on these statements and trends: {json.dumps(results)}"
        #     llm_summary = await self.llm_manager.generate_text(summary_prompt, max_tokens=250)
        #     results["llm_financial_summary"] = llm_summary
            
        return results

    def _calculate_statement_trends(self, statements: List[Dict[str, Any]], stmt_type: str) -> Dict[str, Any]:
        """
        Calculates year-over-year (or period-over-period) growth for key metrics.
        This is a simplified example.
        """
        trends = {}
        # Define key metrics for each statement type
        metrics_to_track = {
            "income_statement": ["totalRevenue", "netIncome", "ebit"],
            "balance_sheet": ["totalAssets", "totalLiabilitiesNetMinorityInterest", "totalEquityGrossMinorityInterest"],
            "cash_flow": ["operatingCashFlow", "freeCashFlow"] # freeCashFlow might need to be calculated
        }

        if stmt_type not in metrics_to_track or not statements:
            return trends

        # Ensure data is sorted by date (most recent first, as typically returned by providers)
        # If not, sort it: statements.sort(key=lambda x: x['date'], reverse=True)
        
        for metric in metrics_to_track[stmt_type]:
            metric_values = [s.get(metric) for s in statements if s.get(metric) is not None]
            if len(metric_values) > 1:
                # Calculate YoY growth for the most recent period
                # Assumes statements are sorted newest to oldest
                current_value = metric_values[0]
                previous_value = metric_values[1]
                if previous_value != 0 and previous_value is not None and current_value is not None: # Avoid division by zero or None
                    growth_rate = ((current_value - previous_value) / abs(previous_value)) * 100
                    trends[f"{metric}_growth_yoy"] = round(growth_rate, 2)
                else:
                    trends[f"{metric}_growth_yoy"] = None
            
            # Could also calculate CAGR over multiple periods
            # cagr = self._calculate_cagr(metric_values)
            # if cagr is not None: trends[f"{metric}_cagr_{len(metric_values)-1}yr"] = cagr
        return trends

    # def _calculate_cagr(self, values: List[float]) -> Optional[float]:
    #     """Calculates Compound Annual Growth Rate. Assumes values are sorted oldest to newest."""
    #     if not values or len(values) < 2 or values[0] is None or values[-1] is None or values[0] == 0:
    #         return None
    #     num_periods = len(values) - 1
    #     return ((values[-1] / values[0]) ** (1 / num_periods) - 1) * 100


    async def perform_valuation_analysis(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Performs basic valuation analysis using common multiples.
        """
        ratios = await self.market_data_service.get_key_financial_ratios(symbol)
        # profile = await self.market_data_service.get_company_profile(symbol) # For sector/industry comparison

        if not ratios:
            return None

        valuation = {"symbol": symbol, "ratios": ratios, "assessment": {}}
        
        # Example: Simple assessment based on P/E (needs industry/sector benchmarks for real value)
        # if ratios.get("pe_ratio") is not None:
        #     if ratios["pe_ratio"] < 15:
        #         valuation["assessment"]["pe_assessment"] = "Potentially Undervalued (Low P/E)"
        #     elif ratios["pe_ratio"] > 25:
        #         valuation["assessment"]["pe_assessment"] = "Potentially Overvalued (High P/E)"
        #     else:
        #         valuation["assessment"]["pe_assessment"] = "Fairly Valued (Moderate P/E)"
        
        # Placeholder for more advanced valuation models (DCF, etc.)
        # dcf_valuation = await self._calculate_dcf(symbol)
        # if dcf_valuation: valuation["dcf"] = dcf_valuation
        
        return valuation

    # Placeholder for DCF calculation
    # async def _calculate_dcf(self, symbol: str) -> Optional[Dict[str, Any]]:
    #     # Fetch FCF, growth rates, WACC etc.
    #     # This is a complex calculation.
    #     return None

    async def get_full_fundamental_report(self, symbol: str) -> Dict[str, Any]:
        """
        Compiles a comprehensive fundamental report.
        """
        overview, financials, valuation = await asyncio.gather(
            self.get_company_overview(symbol),
            self.analyze_financial_statements(symbol, limit=settings.FUNDAMENTAL_ANALYSIS_DEFAULT_PERIODS),
            self.perform_valuation_analysis(symbol)
        )
        
        report = {
            "symbol": symbol,
            "generated_at": datetime.utcnow().isoformat(),
            "company_overview": overview,
            "financial_statement_analysis": financials,
            "valuation_analysis": valuation,
        }
        
        # Optional: LLM summary of the entire report
        # if self.llm_manager:
        #     report_summary_prompt = f"Provide a concise executive summary for the fundamental analysis of {symbol}, based on: {json.dumps(report, default=str)}"
        #     report["executive_summary"] = await self.llm_manager.generate_text(report_summary_prompt, max_tokens=300)
            
        return report

# Example usage (typically called from a higher-level service or API controller):
# async def main():
#     from app.core.cache import RedisCache # Assuming RedisCache is set up
#     cache = RedisCache()
#     md_service = MarketDataService(cache=cache)
#     fund_analyzer = FundamentalAnalyzer(market_data_service=md_service)
    
#     report = await fund_analyzer.get_full_fundamental_report("AAPL")
#     import json
#     print(json.dumps(report, indent=2, default=str))

# if __name__ == "__main__":
#     asyncio.run(main())
