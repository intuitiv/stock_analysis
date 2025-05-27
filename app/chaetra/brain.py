"""Core brain implementation for CHAETRA."""
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import uuid
import asyncio
import json
from dataclasses import dataclass

from app.chaetra.interfaces import (
    MemoryItem,
    Pattern,
    Opinion,
    Intent,
    Evidence,
    IMemorySystem,
    ILearningSystem,
    IReasoningSystem,
    IOpinionSystem,
    ILLMProvider
)
from app.chaetra.memory import MemorySystem
from app.chaetra.learning import LearningSystem
from app.chaetra.reasoning import ReasoningSystem
from app.chaetra.opinion import OpinionSystem
from app.chaetra.llm import LLMManager
from app.chaetra.utils.event_system import get_event_system
from app.schemas.chat_schemas import ProcessingEventType

@dataclass
class ProcessingContext:
    query: str
    intent: Intent
    memories: List[MemoryItem]
    domain_context: Optional[Dict[str, Any]] = None
    available_tools: Optional[Dict[str, Any]] = None
    session_id: Optional[int] = None

class CHAETRA:
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
        self.event_system = get_event_system()

    async def process_input(
        self,
        query: str,
        domain_context: Optional[Dict[str, Any]] = None,
        available_tools: Optional[Dict[str, Any]] = None,
        session_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Main entry point for processing any input query."""
        if not session_id:
            session_id = 0  # Use 0 for sessions without ID
            
        # 1. Understand query intent
        await self.event_system.emit(
            session_id,
            ProcessingEventType.INTENT,
            "Understanding query intent...",
            {"query": query}
        )
        
        intent = await self._understand_query(query, domain_context)
        
        await self.event_system.emit(
            session_id,
            ProcessingEventType.INTENT,
            "Query intent understood",
            intent.__dict__
        )
        
        # 2. Retrieve relevant memories
        await self.event_system.emit(
            session_id,
            ProcessingEventType.PROCESSING,
            "Retrieving relevant memories...",
            {"intent": intent.primary_goal}
        )
        
        memories = await self._retrieve_relevant_memories(intent)
        
        await self.event_system.emit(
            session_id,
            ProcessingEventType.PROCESSING,
            "Memory retrieval complete",
            {
                "memory_count": len(memories),
                "relevance_scores": [m.relevance for m in memories]
            }
        )
        
        # 3. Create processing context
        context = ProcessingContext(
            query=query,
            intent=intent,
            memories=memories,
            domain_context=domain_context,
            available_tools=available_tools,
            session_id=session_id
        )
        
        # 4. Process the query
        await self.event_system.emit(
            session_id,
            ProcessingEventType.ANALYSIS,
            "Starting query analysis...",
            {"context_size": len(memories)}
        )
        
        result = await self._process_with_context(context)
        
        # 5. Learn from interaction
        await self.event_system.emit(
            session_id,
            ProcessingEventType.LEARNING,
            "Learning from interaction...",
            {"interaction_id": str(uuid.uuid4())}
        )
        
        await self._learn_from_interaction(context, result)
        
        # Return final result
        return result

    async def _understand_query(
        self,
        query: str,
        domain_context: Optional[Dict[str, Any]]
    ) -> Intent:
        """Understand the core intent of any query."""
        schema = {
            "type": "object",
            "properties": {
                "primary_goal": {"type": "string", "description": "The fundamental goal of the query"},
                "sub_goals": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of secondary objectives"
                },
                "required_context": {
                    "type": "object",
                    "description": "Required contextual information as key-value pairs"
                },
                "metadata": {
                    "type": "object",
                    "properties": {
                        "response_type": {
                            "type": "string",
                            "enum": ["info", "analysis", "opinion"],
                            "default": "info"
                        },
                        "domain": {
                            "type": "string",
                            "default": "market"
                        },
                        "additional": {
                            "type": "object",
                            "additionalProperties": True
                        }
                    },
                    "additionalProperties": False,
                    "default": {
                        "response_type": "info",
                        "domain": "market",
                        "additional": {}
                    }
                }
            },
            "required": ["primary_goal", "sub_goals", "required_context"]
        }
        
        prompt = f"""
        YOUR TASK: Analyze the following query and return a STRICT JSON object matching the provided schema.
        DO NOT include any explanatory text, markdown, or other formatting - ONLY return the JSON object.
        
        Query: "{query}"
        Additional Context: {domain_context if domain_context else 'None'}
        
        EXAMPLE OUTPUT:
        {{
            "primary_goal": "get stock price information",
            "sub_goals": ["check current price", "view price history"],
            "required_context": {{
                "symbol": "AAPL",
                "time_range": "1d"
            }},
            "metadata": {{
                "response_type": "analysis",
                "domain": "market",
                "additional": {{
                    "analysis_type": "price",
                    "data_source": "market"
                }}
            }}
        }}
        
        REQUIREMENTS:
        1. Response must be valid JSON - use ONLY the fields defined in the schema
        2. Include all required fields: primary_goal, sub_goals, and required_context
        3. required_context must be an object with key-value pairs
        4. metadata is optional but must be an object if included
        5. No explanatory text or other content outside the JSON object
        """
        
        try:
            # Get JSON response from LLM
            intent_data = await self.llm.generate_structured_output(prompt, schema)
            
            # Log the raw LLM response for debugging
            logger = logging.getLogger(__name__)
            logger.debug(f"LLM Response: {intent_data}")
            
            # Provide defaults for required fields if missing
            default_context = {"query": query}
            
            # Create base intent data with defaults
            processed_intent = {
                "primary_goal": intent_data.get('primary_goal', "process user query"),
                "sub_goals": intent_data.get('sub_goals', ["understand request"]),
                "required_context": intent_data.get('required_context', default_context),
                "metadata": intent_data.get('metadata', {
                    "response_type": "info",
                    "domain": "market",
                    "additional": {}
                })
            }
            
            # Extract response_type from metadata
            metadata = processed_intent["metadata"]
            response_type = metadata.get('response_type', 'info')
            
            # Create Intent with processed fields
            return Intent(
                primary_goal=processed_intent["primary_goal"],
                sub_goals=processed_intent["sub_goals"],
                required_context=processed_intent["required_context"],
                metadata=metadata,
                response_type=response_type
            )
            
        except Exception as e:
            logger.error(f"Error processing LLM response: {e}", exc_info=True)
            # Return a default intent on failure
            return Intent(
                primary_goal="process user query",
                sub_goals=["understand request"],
                required_context={"query": query},
                metadata={"response_type": "info", "domain": "market", "additional": {}},
                response_type="info"
            )

    async def _retrieve_relevant_memories(
        self,
        intent: Intent
    ) -> List[MemoryItem]:
        """Retrieve memories relevant to the current query."""
        memory_query = {
            "relevance_to": intent.primary_goal,
            "context_match": intent.required_context,
            "recency_weight": 0.7,
            "confidence_threshold": 0.5
        }
        
        return await self.memory.retrieve_memory(
            query=memory_query,
            limit=10
        )

    async def _process_with_context(
        self,
        context: ProcessingContext
    ) -> Dict[str, Any]:
        """Process query with full context."""
        session_id = context.session_id or 0
        
        # 1. Initial reasoning based on memories
        await self.event_system.emit(
            session_id,
            ProcessingEventType.THOUGHT,
            "Analyzing available information...",
            {"memory_count": len(context.memories)}
        )
        
        reasoning_result = await self.reasoning.analyze(
            query=context.query,
            intent=context.intent,
            memories=context.memories,
            available_tools=context.available_tools
        )
        
        await self.event_system.emit(
            session_id,
            ProcessingEventType.THOUGHT,
            "Initial analysis complete",
            {
                "confidence": reasoning_result.get("confidence", 0.0),
                "has_conclusion": bool(reasoning_result.get("conclusion"))
            }
        )
        
        # 2. Form opinion if needed
        opinion = None
        if context.intent.response_type in ["opinion", "analysis"]:
            await self.event_system.emit(
                session_id,
                ProcessingEventType.THOUGHT,
                "Forming opinion based on analysis...",
                {"analysis_type": context.intent.response_type}
            )
            
            opinion = await self.opinion.form_opinion(
                subject=context.query,
                reasoning_result=reasoning_result,
                context=context.domain_context
            )
            
            await self.event_system.emit(
                session_id,
                ProcessingEventType.THOUGHT,
                "Opinion formed",
                {
                    "confidence": opinion.confidence if opinion else 0.0,
                    "has_summary": bool(opinion and opinion.summary)
                }
            )
        
        # 3. Compile final response
        return {
            "query_understanding": context.intent.__dict__,
            "reasoning_process": reasoning_result,
            "formed_opinion": opinion.__dict__ if opinion else None,
            "confidence": reasoning_result.get("confidence", 0.0),
            "processing_metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "used_memories": len(context.memories),
                "used_tools": bool(context.available_tools)
            }
        }

    async def _learn_from_interaction(
        self,
        context: ProcessingContext,
        result: Dict[str, Any]
    ) -> None:
        """Learn from the current interaction."""
        session_id = context.session_id or 0
        
        # Prepare learning data
        learning_data = {
            "interaction_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "query_data": {
                "raw_query": context.query,
                "parsed_intent": context.intent.__dict__,
                "domain_context": context.domain_context
            },
            "processing_data": {
                "used_memories": [m.id for m in context.memories],
                "reasoning_path": result.get("reasoning_process", {}).get("path", []),
                "confidence": result.get("confidence", 0.0)
            },
            "outcome_data": {
                "success": bool(result),
                "response_type": context.intent.response_type or "info",
                "confidence": result.get("confidence", 0.0)
            }
        }
        
        await self.learning.learn_from_interaction(learning_data)
        
        await self.event_system.emit(
            session_id,
            ProcessingEventType.LEARNING,
            "Learning complete",
            {
                "interaction_id": learning_data["interaction_id"],
                "confidence": learning_data["outcome_data"]["confidence"]
            }
        )
