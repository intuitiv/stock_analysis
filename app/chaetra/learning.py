"""Learning system for improving responses based on interactions."""
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from app.chaetra.interfaces import (
    ILearningSystem,
    Pattern
)
from app.chaetra.utils.event_system import get_event_system
from app.schemas.chat_schemas import ProcessingEventType

class LearningSystem(ILearningSystem):
    def __init__(self):
        """Initialize learning system."""
        self.event_system = get_event_system()
        self.patterns: Dict[str, Pattern] = {}
        self.interaction_history: List[Dict[str, Any]] = []
        
    async def learn_from_interaction(
        self,
        interaction_data: Dict[str, Any]
    ) -> None:
        """Learn from an interaction."""
        session_id = (
            interaction_data.get("query_data", {})
            .get("domain_context", {})
            .get("session_id", 0)
        )
        
        # 1. Store interaction
        await self.event_system.emit(
            session_id,
            ProcessingEventType.LEARNING,
            "Recording interaction...",
            {"interaction_id": interaction_data.get("interaction_id")}
        )
        
        self.interaction_history.append(interaction_data)
        
        # 2. Extract patterns
        await self.event_system.emit(
            session_id,
            ProcessingEventType.LEARNING,
            "Analyzing patterns...",
            {"history_size": len(self.interaction_history)}
        )
        
        new_patterns = await self._extract_patterns(interaction_data)
        
        # 3. Update pattern database
        for pattern in new_patterns:
            pattern_key = f"{pattern.pattern_type}:{json.dumps(pattern.data)}"
            
            if pattern_key in self.patterns:
                # Update existing pattern confidence
                existing = self.patterns[pattern_key]
                updated_confidence = (
                    existing.confidence * 0.8 +  # Weight history
                    pattern.confidence * 0.2     # Weight new observation
                )
                existing.confidence = min(1.0, updated_confidence)
                
                if existing.metadata is None:
                    existing.metadata = {}
                existing.metadata["last_updated"] = datetime.utcnow().isoformat()
                existing.metadata["observation_count"] = (
                    existing.metadata.get("observation_count", 1) + 1
                )
            else:
                # Store new pattern
                self.patterns[pattern_key] = pattern
                
        await self.event_system.emit(
            session_id,
            ProcessingEventType.LEARNING,
            "Learning complete",
            {
                "new_patterns": len(new_patterns),
                "total_patterns": len(self.patterns)
            }
        )
        
    async def get_learned_patterns(self) -> List[Pattern]:
        """Get learned patterns."""
        return list(self.patterns.values())
        
    async def _extract_patterns(
        self,
        interaction_data: Dict[str, Any]
    ) -> List[Pattern]:
        """Extract patterns from interaction data."""
        patterns = []
        
        # Extract query patterns
        if query_data := interaction_data.get("query_data"):
            if intent := query_data.get("parsed_intent"):
                patterns.append(Pattern(
                    pattern_type="query_intent",
                    data={
                        "goal": intent.get("primary_goal"),
                        "context": intent.get("required_context")
                    },
                    confidence=0.7,
                    metadata={
                        "timestamp": datetime.utcnow().isoformat(),
                        "pattern_source": "intent_parsing"
                    }
                ))
                
        # Extract processing patterns
        if processing_data := interaction_data.get("processing_data"):
            if reasoning_path := processing_data.get("reasoning_path"):
                patterns.append(Pattern(
                    pattern_type="reasoning_flow",
                    data={"path": reasoning_path},
                    confidence=processing_data.get("confidence", 0.5),
                    metadata={
                        "timestamp": datetime.utcnow().isoformat(),
                        "pattern_source": "reasoning_analysis"
                    }
                ))
                
        # Extract outcome patterns
        if outcome_data := interaction_data.get("outcome_data"):
            patterns.append(Pattern(
                pattern_type="interaction_outcome",
                data={
                    "success": outcome_data.get("success", False),
                    "response_type": outcome_data.get("response_type")
                },
                confidence=outcome_data.get("confidence", 0.5),
                metadata={
                    "timestamp": datetime.utcnow().isoformat(),
                    "pattern_source": "outcome_analysis"
                }
            ))
            
        return patterns
        
    def _get_pattern_summary(self) -> Dict[str, Any]:
        """Get summary of learned patterns."""
        summary = {
            "total_patterns": len(self.patterns),
            "pattern_types": {},
            "average_confidence": 0.0,
            "high_confidence_patterns": 0
        }
        
        if not self.patterns:
            return summary
            
        # Analyze patterns
        confidence_sum = 0
        for pattern in self.patterns.values():
            # Count pattern types
            pattern_type = pattern.pattern_type
            summary["pattern_types"][pattern_type] = (
                summary["pattern_types"].get(pattern_type, 0) + 1
            )
            
            # Track confidence
            confidence_sum += pattern.confidence
            if pattern.confidence > 0.8:
                summary["high_confidence_patterns"] += 1
                
        summary["average_confidence"] = confidence_sum / len(self.patterns)
        
        return summary
