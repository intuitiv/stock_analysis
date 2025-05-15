from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import json # For formatting prompts if needed

# Assuming FastAPI's Depends for dependency injection if this were part of an API
# from fastapi import Depends 

from app.core.config import settings
# from app.core.database import get_db # If direct DB access needed here
from app.chaetra.interfaces import MemoryItem, Pattern, Opinion # Import dataclasses
from app.chaetra.memory import MemorySystem
from app.chaetra.learning import LearningSystem
from app.chaetra.reasoning import ReasoningSystem
from app.chaetra.opinion import OpinionSystem
from app.chaetra.llm import LLMManager

class CHAETRA:
    _instance: Optional['CHAETRA'] = None

    @classmethod
    async def get_instance(
        cls,
        memory_system: Optional[MemorySystem] = None,
        learning_system: Optional[LearningSystem] = None,
        reasoning_system: Optional[ReasoningSystem] = None,
        opinion_system: Optional[OpinionSystem] = None,
        llm_manager: Optional[LLMManager] = None
    ) -> 'CHAETRA':
        if cls._instance is None:
            # Initialize dependencies if not provided (suitable for standalone use or testing)
            # In a FastAPI app, these would typically be injected.
            mem_sys = memory_system or MemorySystem()
            llm_mgr = llm_manager or await LLMManager.create()
            learn_sys = learning_system or LearningSystem(mem_sys)
            reason_sys = reasoning_system or ReasoningSystem(mem_sys, learn_sys, llm_mgr)
            op_sys = opinion_system or OpinionSystem(mem_sys, llm_mgr)
            
            cls._instance = cls(
                memory_system=mem_sys,
                learning_system=learn_sys,
                reasoning_system=reason_sys,
                opinion_system=op_sys,
                llm_manager=llm_mgr
            )
        return cls._instance

    def __init__(
        self,
        memory_system: MemorySystem,
        learning_system: LearningSystem,
        reasoning_system: ReasoningSystem,
        opinion_system: OpinionSystem,
        llm_manager: LLMManager
    ):
        self.memory = memory_system
        self.learning = learning_system
        self.reasoning = reasoning_system
        self.opinion = opinion_system
        self.llm = llm_manager
        print("[CHAETRA Brain] Initialized.")

    async def understand_query_intent(
        self,
        query_text: str,
        chat_context: Optional[Dict[str, Any]] = None, # e.g., current symbols, timeframe from chat
        provider_name: Optional[str] = None  # Specify LLM provider
    ) -> Dict[str, Any]:
        """
        Uses LLM to parse the user's query into a structured intent.
        """
        print(f"[CHAETRA Brain] Understanding query: '{query_text}'")
        # Define a schema for the expected intent structure
        intent_schema = {
            "query_type": "str (e.g., 'stock_price', 'market_sentiment', 'technical_analysis', 'compare_stocks', 'portfolio_status')",
            "entities": {
                "symbols": "List[str] (stock tickers like AAPL, MSFT)",
                "indicators": "List[str] (technical indicators like RSI, MACD)",
                "timeframe": "Optional[str] (e.g., '1D', '1W', 'YTD')",
                "keywords": "List[str] (other relevant keywords from query)"
            },
            "user_goal": "str (inferred goal of the user, e.g., 'assess risk', 'find buy opportunity')"
        }
        
        prompt = f"""
        Parse the following user query into a structured intent based on the provided schema.
        Identify stock symbols (assume uppercase are symbols), technical indicators, timeframes, and other keywords.
        Infer the primary goal of the user.

        User Query: "{query_text}"
        
        Chat Context (if any, for disambiguation): {json.dumps(chat_context) if chat_context else "None"}

        Output JSON matching this schema:
        {json.dumps(intent_schema, indent=2)}
        """
        
        try:
            structured_intent = await self.llm.generate_structured_output(
                prompt,
                schema=intent_schema,
                provider_name=provider_name
            )
            # Basic validation/cleanup
            if not isinstance(structured_intent.get("entities"), dict):
                structured_intent["entities"] = {}
            for key in ["symbols", "indicators", "keywords"]:
                if not isinstance(structured_intent["entities"].get(key), list):
                    structured_intent["entities"][key] = []
            
            print(f"[CHAETRA Brain] Parsed Intent: {structured_intent}")
            return structured_intent
        except Exception as e:
            print(f"[CHAETRA Brain] Error parsing query intent: {e}")
            return {"query_type": "unknown", "entities": {}, "user_goal": "unknown", "error": str(e)}


    async def process_data_and_generate_analysis(
        self,
        input_data: Dict[str, Any], # This would be data fetched by NAETRA layer (market data, news, etc.)
        query_intent: Dict[str, Any], # Output from understand_query_intent
        request_context: Dict[str, Any] # Overall context (user profile, settings)
    ) -> Dict[str, Any]:
        """
        Main processing pipeline after NAETRA has fetched necessary data.
        """
        print(f"[CHAETRA Brain] Processing data for intent: {query_intent.get('query_type')}")
        
        # 1. Reasoning System analyzes data based on intent and context
        analysis_result = await self.reasoning.analyze_data(input_data, request_context, query_intent)
        
        # 2. Opinion System forms opinions based on the analysis
        # Topic for opinion could be derived from query_intent or be more general
        topic = query_intent.get("entities", {}).get("symbols", [])
        topic_str = ", ".join(topic) if topic else query_intent.get("query_type", "general_market")
        
        formed_opinion = await self.opinion.form_opinion(
            topic=f"{topic_str} ({query_intent.get('query_type', '')})", # Make topic more specific
            analysis_result=analysis_result,
            context=request_context
        )
        
        # 3. Generate Trading Suggestion (if applicable based on intent/analysis)
        trading_suggestion = None
        if query_intent.get("user_goal") in ["find_buy_opportunity", "find_sell_opportunity", "assess_trade"] or \
           formed_opinion.confidence > 0.7: # Example condition
            trading_suggestion = await self.reasoning.generate_trading_suggestion(
                analysis_result=analysis_result,
                current_portfolio=request_context.get("portfolio_snapshot"), # NAETRA needs to provide this
                risk_profile=request_context.get("user_risk_profile", "moderate") # NAETRA provides this
            )

        # 4. Store key findings/analysis in memory
        await self.memory.add_to_short_term(
            content={
                "type": "analysis_session",
                "query_intent": query_intent,
                "input_data_summary": {k:type(v).__name__ for k,v in input_data.items()},
                "analysis_summary": analysis_result.get("analysis_summary"),
                "opinion_belief": formed_opinion.belief,
                "opinion_confidence": formed_opinion.confidence,
                "trading_suggestion": trading_suggestion
            },
            source="chaetra_processing",
            tags=query_intent.get("entities", {}).get("symbols", []) + [query_intent.get("query_type", "analysis")]
        )
        
        return {
            "analysis": analysis_result,
            "opinion": formed_opinion.__dict__, # Convert dataclass to dict for serialization
            "trading_suggestion": trading_suggestion,
        }

    async def learn_from_interaction_outcome(
        self,
        interaction_data: Dict[str, Any], # Query, context, data used, CHAETRA's response (analysis, opinion)
        actual_outcome: Dict[str, Any] # What actually happened in the market, or user feedback
    ) -> None:
        """
        Allows CHAETRA to learn from the outcomes of its predictions or analyses.
        """
        print(f"[CHAETRA Brain] Learning from outcome: {actual_outcome}")
        
        previous_opinion_data = interaction_data.get("chaetra_response", {}).get("opinion")
        previous_opinion = Opinion(**previous_opinion_data) if previous_opinion_data else None
        
        data_context_for_learning = {
            "query_intent": interaction_data.get("query_intent"),
            "input_data": interaction_data.get("input_data_summary"), # Use summary or full data if feasible
            "request_context": interaction_data.get("request_context"),
            "symbol": interaction_data.get("request_context",{}).get("symbol") # Helper for learning system
        }

        await self.learning.learn_from_outcome(
            data_context=data_context_for_learning,
            outcome=actual_outcome,
            previous_opinion=previous_opinion
        )
        
        # Potentially update the original opinion's confidence or add contradictory evidence
        if previous_opinion:
            # This is simplified. A real update might involve more nuanced evidence processing.
            evidence_from_outcome = {
                "type": "observed_outcome",
                "content": actual_outcome,
                "source": "feedback_loop",
                "matches_belief": actual_outcome.get("matches_belief", False) # Assuming outcome has this
            }
            await self.opinion.update_opinion(previous_opinion.id, new_evidence=[evidence_from_outcome])


    async def get_system_status_and_recent_learnings(self) -> Dict[str, Any]:
        # Example of providing some insight into CHAETRA's state
        recent_core_memories = await self.memory.retrieve_memory(query={}, memory_type='core', limit=3)
        recent_patterns = await self.memory.retrieve_memory(query={'type': 'core_pattern'}, memory_type='core', limit=3)
        
        return {
            "status": "Operational",
            "default_llm_provider": self.llm.default_provider_name,
            "recent_core_memories_count": len(recent_core_memories), # This would be a total count in reality
            "recent_patterns_learned_count": len(recent_patterns), # Total count
            "sample_recent_patterns": [Pattern(**p.content).name for p in recent_patterns]
        }

    # --- Helper methods for prompt creation (can be expanded) ---
    def _create_intent_prompt(self, query_text: str) -> str:
        # This is now part of understand_query_intent to include schema directly
        return query_text # The full prompt is constructed in understand_query_intent

    def _create_insights_prompt(self, combined_data: Dict[str, Any]) -> str:
        # Simplified prompt for generating insights
        prompt = f"""
        Based on the following analysis and opinions:
        Analysis Summary: {combined_data.get('analysis', {}).get('analysis_summary', 'N/A')}
        Opinions: 
        """
        for op_data in combined_data.get('opinions', []):
            # op = Opinion(**op_data) # If it's dict
            op = op_data # If it's already Opinion object
            prompt += f"- Topic: {op.topic}, Belief: {op.belief} (Confidence: {op.confidence:.2f})\n"
        
        prompt += f"\nUser Query Intent: {combined_data.get('intent', {}).get('query_type', 'N/A')} for {combined_data.get('intent', {}).get('entities', {}).get('symbols', [])}"
        prompt += "\n\nGenerate key insights and actionable takeaways. Be concise."
        return prompt

    async def _enrich_intent(self, intent: Dict[str, Any], context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        # Placeholder: Use context to refine intent, e.g., resolve ambiguities
        if context and not intent.get("entities", {}).get("symbols") and context.get("current_symbol"):
            if "entities" not in intent: intent["entities"] = {}
            intent["entities"]["symbols"] = [context["current_symbol"]]
        return intent

    async def _validate_intent(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        # Placeholder: Check if CHAETRA can handle this type of query
        # e.g., if query_type is 'unsupported_feature', modify or flag it
        if intent.get("query_type") == "make_coffee":
            intent["can_handle"] = False
            intent["error_message"] = "I cannot make coffee, but I can analyze stocks!"
        else:
            intent["can_handle"] = True
        return intent

    async def _structure_insights(self, insights_text: str, combined_data: Dict[str, Any]) -> Dict[str, Any]:
        # Placeholder: Parse LLM insights_text into a structured format if needed
        # For now, return as text, but could involve schema-based parsing
        return {
            "narrative": insights_text,
            "key_points": [p.strip() for p in insights_text.split("\n") if p.strip() and (p.startswith("-") or p.startswith("*"))][:5], # Simple extraction
            "related_patterns": [p.get('name') for p in combined_data.get('analysis',{}).get('identified_patterns',[])[:3]],
            "primary_opinion_topic": combined_data.get('opinions',[{}])[0].get('topic', 'N/A')
        }

# To make CHAETRA usable as a singleton dependency in FastAPI:
# chaetra_instance = CHAETRA.get_instance()
# def get_chaetra_instance():
#     return chaetra_instance
# Then in API routes: brain: CHAETRA = Depends(get_chaetra_instance)
