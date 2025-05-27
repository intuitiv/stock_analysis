"""Opinion system for forming conclusions based on analysis."""
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.chaetra.interfaces import (
    IOpinionSystem,
    Opinion,
    Evidence
)
from app.chaetra.utils.event_system import get_event_system
from app.schemas.chat_schemas import ProcessingEventType

class OpinionSystem(IOpinionSystem):
    def __init__(self):
        """Initialize opinion system."""
        self.event_system = get_event_system()
        
    async def form_opinion(
        self,
        subject: str,
        reasoning_result: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Opinion]:
        """Form an opinion based on analysis."""
        session_id = context.get("session_id", 0) if context else 0
        
        # 1. Extract evidence from reasoning
        await self.event_system.emit(
            session_id,
            ProcessingEventType.THOUGHT,
            "Evaluating evidence...",
            {"reasoning_confidence": reasoning_result.get("confidence", 0.0)}
        )
        
        evidence = self._extract_evidence(reasoning_result)
        if not evidence:
            await self.event_system.emit(
                session_id,
                ProcessingEventType.THOUGHT,
                "Insufficient evidence to form opinion",
                {"status": "no_evidence"}
            )
            return None
            
        # 2. Weigh evidence
        evidence_weights = await self._weigh_evidence(evidence, context)
        
        # 3. Form summary
        summary = await self._form_summary(
            subject,
            evidence,
            evidence_weights,
            reasoning_result
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            evidence_weights,
            reasoning_result.get("confidence", 0.0)
        )
        
        await self.event_system.emit(
            session_id,
            ProcessingEventType.THOUGHT,
            "Opinion formed",
            {
                "confidence": confidence,
                "evidence_count": len(evidence)
            }
        )
        
        # Return formed opinion
        return Opinion(
            subject=subject,
            summary=summary,
            confidence=confidence,
            evidence=evidence,
            metadata={
                "timestamp": datetime.utcnow().isoformat(),
                "evidence_weights": evidence_weights,
                "context_type": context.get("analysis_type") if context else None
            }
        )
        
    def _extract_evidence(self, reasoning_result: Dict[str, Any]) -> List[Evidence]:
        """Extract evidence from reasoning results."""
        evidence = []
        
        # Extract from reasoning path
        if path := reasoning_result.get("path", []):
            for step in path:
                if "evidence" in step.lower():
                    evidence.append(Evidence(
                        source="reasoning_path",
                        data={"step": step},
                        confidence=reasoning_result.get("confidence", 0.5),
                        timestamp=datetime.utcnow()
                    ))
                    
        # Extract from patterns
        if patterns := reasoning_result.get("patterns", []):
            for pattern in patterns:
                evidence.append(Evidence(
                    source="pattern_analysis",
                    data=pattern,
                    confidence=pattern.get("confidence", 0.5),
                    timestamp=datetime.utcnow()
                ))
                
        # Extract from insights
        if insights := reasoning_result.get("insights", []):
            for insight in insights:
                evidence.append(Evidence(
                    source="insight_analysis",
                    data={"insight": insight},
                    confidence=reasoning_result.get("confidence", 0.5),
                    timestamp=datetime.utcnow()
                ))
                
        return evidence
    
    async def _weigh_evidence(
        self,
        evidence: List[Evidence],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Weigh evidence based on source and context."""
        weights = {}
        
        # Base weights for different sources
        source_weights = {
            "market_data": 0.8,
            "technical_analysis": 0.7,
            "fundamental_analysis": 0.7,
            "sentiment_analysis": 0.5,
            "pattern_analysis": 0.6,
            "insight_analysis": 0.5,
            "reasoning_path": 0.4
        }
        
        # Adjust weights based on context
        context_type = context.get("analysis_type") if context else None
        
        for e in evidence:
            base_weight = source_weights.get(e.source, 0.5)
            
            # Boost weight if source matches context
            if context_type and context_type in e.source:
                base_weight *= 1.2
                
            # Factor in confidence
            final_weight = base_weight * e.confidence
            
            weights[str(e.data)] = min(1.0, final_weight)
            
        return weights
    
    async def _form_summary(
        self,
        subject: str,
        evidence: List[Evidence],
        weights: Dict[str, float],
        reasoning_result: Dict[str, Any]
    ) -> str:
        """Form a summary opinion based on weighted evidence."""
        # Get overall sentiment
        sentiment_score = sum(
            weights.get(str(e.data), 0.5) * e.confidence
            for e in evidence
        ) / len(evidence) if evidence else 0.5
        
        # Form summary based on mock templates
        if sentiment_score > 0.7:
            return (
                f"Strong positive indicators for {subject}. "
                "Evidence suggests favorable conditions with high confidence."
            )
        elif sentiment_score > 0.5:
            return (
                f"Moderately positive outlook for {subject}. "
                "Some supporting evidence, but continue monitoring."
            )
        else:
            return (
                f"Neutral stance on {subject}. "
                "Insufficient evidence for strong recommendation."
            )
            
    def _calculate_confidence(
        self,
        evidence_weights: Dict[str, float],
        reasoning_confidence: float
    ) -> float:
        """Calculate overall confidence in the opinion."""
        if not evidence_weights:
            return 0.0
            
        # Average evidence weights
        evidence_confidence = sum(evidence_weights.values()) / len(evidence_weights)
        
        # Combine with reasoning confidence
        return min(1.0, (evidence_confidence + reasoning_confidence) / 2)
