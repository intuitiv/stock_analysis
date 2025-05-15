"""Reasoning system implementation for CHAETRA."""
from typing import Dict, Any, List
from datetime import datetime
import json
from app.chaetra.interfaces import IReasoningSystem
from app.chaetra.llm import LLMManager
from app.chaetra.memory import MemorySystem
from app.chaetra.learning import LearningSystem
from app.chaetra.utils.DateTimeEncoder import DateTimeEncoder


class ReasoningSystem(IReasoningSystem):
    """Implementation of the reasoning system."""
    
    def __init__(
        self,
        memory_system: MemorySystem,
        learning_system: LearningSystem,
        llm_manager: LLMManager
    ):
        self.memory = memory_system
        self.learning = learning_system
        self.llm = llm_manager
        self.min_confidence = 0.7

    async def analyze_data(
        self,
        data: Dict[str, Any],
        context: Dict[str, Any],
        query_intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze data and generate insights."""
        
        # Prepare analysis prompt based on query type
        query_type = query_intent.get("query_type", "general")
        if query_type == "technical_analysis":
            prompt = self._create_technical_analysis_prompt(data, context)
        elif query_type == "fundamental_analysis":
            prompt = self._create_fundamental_analysis_prompt(data, context)
        elif query_type == "market_sentiment":
            prompt = self._create_sentiment_analysis_prompt(data, context)
        else:
            prompt = self._create_general_analysis_prompt(data, context)

        # Generate analysis using LLM
        analysis_text = await self.llm.generate_text(
            prompt=prompt,
            context=context,
            temperature=0.3  # Lower temperature for more focused analysis
        )

        # Structure the analysis results
        result = {
            "analysis_summary": analysis_text,
            "timestamp": datetime.utcnow().isoformat(),
            "data_analyzed": {k: str(type(v).__name__) for k, v in data.items()},
            "query_type": query_type,
            "confidence": self.min_confidence,
            "insights": [],
            "charts_for_frontend": self._extract_chart_recommendations(data)
        }

        # Store analysis in memory
        await self.memory.add_to_short_term(
            content=result,
            source="reasoning_analysis",
            tags=[query_type, *context.get("current_symbols", [])]
        )

        return result

    async def generate_trading_suggestion(
        self,
        analysis_result: Dict[str, Any],
        current_portfolio: Dict[str, Any],
        risk_profile: str
    ) -> Dict[str, Any]:
        """Generate trading suggestions based on analysis."""
        context = {
            "analysis": analysis_result,
            "portfolio": current_portfolio,
            "risk_profile": risk_profile
        }

        prompt = """
        Based on the analysis and considering the current portfolio and risk profile,
        generate specific trading suggestions. Include:
        1. Recommended actions (buy/sell/hold)
        2. Risk assessment
        3. Position size recommendations
        4. Entry/exit points if applicable
        """

        suggestion_text = await self.llm.generate_text(
            prompt=prompt,
            context=context,
            temperature=0.2  # Very low temperature for conservative suggestions
        )

        return {
            "suggestion": suggestion_text,
            "risk_profile": risk_profile,
            "analysis_timestamp": analysis_result.get("timestamp"),
            "confidence": self.min_confidence
        }

    def _create_technical_analysis_prompt(self, data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Create prompt for technical analysis."""
        return f"""
        Analyze the technical indicators and price action for {context.get('current_symbol')}:
        
        Technical Data:
        {json.dumps(data.get('technical_data', {}), indent=2)}
        
        Consider:
        1. Trend analysis (short, medium, long term)
        2. Support and resistance levels
        3. Technical indicator signals
        4. Pattern formations
        5. Volume analysis
        6. Momentum indicators
        
        Provide a comprehensive technical analysis with specific insights and predictions.
        """

    def _create_fundamental_analysis_prompt(self, data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Create prompt for fundamental analysis."""
        return f"""
        Analyze the fundamental data for {context.get('current_symbol')}:
        
        Financial Data:
        {json.dumps(data.get('fundamental_data', {}), indent=2)}
        
        Consider:
        1. Financial ratios
        2. Growth metrics
        3. Industry comparison
        4. Business model strength
        5. Market position
        6. Risk factors
        
        Provide a comprehensive fundamental analysis with specific insights about the company's value.
        """

    def _create_sentiment_analysis_prompt(self, data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Create prompt for sentiment analysis."""
        return f"""
        Analyze market sentiment for {context.get('current_symbol')}:
        
        Sentiment Data:
        {json.dumps(data.get('sentiment_data', {}), indent=2)}
        
        Consider:
        1. News sentiment
        2. Social media trends
        3. Analyst opinions
        4. Market sentiment indicators
        5. Institutional activity
        
        Provide a comprehensive sentiment analysis with specific insights about market perception.
        """

    def _create_general_analysis_prompt(self, data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Create prompt for general analysis."""
        return f"""
        Provide a comprehensive analysis of {context.get('current_symbol')}:
        
        Available Data:
        {json.dumps(data, indent=2, cls=DateTimeEncoder)}
        
        Consider:
        1. Overall market context
        2. Available technical signals
        3. Fundamental factors
        4. Market sentiment
        5. Risk factors
        
        Provide a balanced analysis combining all available information.
        """

    def _extract_chart_recommendations(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract chart recommendations for frontend visualization."""
        # This would be implemented based on your frontend charting library
        return []
