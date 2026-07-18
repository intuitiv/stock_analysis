"""Opinion system implementation for CHAETRA."""
import uuid
import json
from typing import Dict, Any, List
from datetime import datetime

from app.chaetra.interfaces import IOpinionSystem, Opinion
from app.chaetra.memory import MemorySystem
from app.chaetra.llm import LLMManager

class OpinionSystem(IOpinionSystem):
    """Implementation of the opinion system."""
    
    def __init__(self, memory_system: MemorySystem, llm_manager: LLMManager):
        self.memory = memory_system
        self.llm = llm_manager
        self.min_confidence = 0.6

    async def form_opinion(
        self,
        topic: str,
        analysis_result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Opinion:
        """Form an opinion about a topic based on analysis."""
        
        # Generate opinion using LLM
        prompt = self._create_opinion_prompt(topic, analysis_result, context)
        opinion_text = await self.llm.generate_text(
            prompt=prompt,
            context=context,
            temperature=0.3
        )

        # Calculate confidence based on analysis and evidence
        confidence = self._calculate_confidence(analysis_result)

        # Create opinion object
        opinion = Opinion(
            id=uuid.uuid4(),
            topic=topic,
            belief=opinion_text,
            confidence=confidence,
            evidence=[
                {
                    "type": "analysis_result",
                    "content": analysis_result,
                    "timestamp": datetime.utcnow().isoformat()
                }
            ],
            formed_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            validation_count=1,
            metadata={
                "context": context,
                "source": "initial_analysis"
            }
        )

        # Store opinion in memory if confidence meets threshold
        if confidence >= self.min_confidence:
            try:
                await self.memory.add_to_short_term(
                    content={
                        **opinion.__dict__,
                        "id": str(opinion.id)  # Convert UUID to string for serialization
                    },
                    source="opinion_formation",
                    tags=[topic, *context.get("current_symbols", [])]
                )
            except Exception as e:
                print(f"Failed to store opinion in memory: {str(e)}")

        return opinion

    async def update_opinion(
        self,
        opinion_id: uuid.UUID,
        new_evidence: List[Dict[str, Any]]
    ) -> Opinion:
        """Update an existing opinion with new evidence."""
        
        # Retrieve existing opinion from memory
        opinions = await self.memory.retrieve_memory(
            query={"id": str(opinion_id)},
            memory_type="all",
            limit=1
        )
        
        if not opinions:
            raise ValueError(f"Opinion {opinion_id} not found")
        
        # Convert memory item to Opinion object
        memory_content = opinions[0].content
        memory_content["id"] = uuid.UUID(memory_content["id"])  # Convert string back to UUID
        current_opinion = Opinion(**memory_content)
        
        # Add new evidence
        current_opinion.evidence.extend(new_evidence)
        current_opinion.validation_count += 1
        current_opinion.last_updated = datetime.utcnow()
        
        # Recalculate confidence
        new_confidence = self._recalculate_confidence(
            current_confidence=current_opinion.confidence,
            validation_count=current_opinion.validation_count,
            new_evidence=new_evidence
        )
        current_opinion.confidence = new_confidence

        # Update in memory
        try:
            await self.memory.add_to_short_term(
                content={
                    **current_opinion.__dict__,
                    "id": str(current_opinion.id)  # Convert UUID to string for serialization
                },
                source="opinion_update",
                tags=[current_opinion.topic]
            )

            # If confidence and validation count are high enough, move to core memory
            if (current_opinion.confidence >= 0.8 and 
                current_opinion.validation_count >= 3):
                await self.memory.move_to_core(opinions[0])
        except Exception as e:
            print(f"Failed to update opinion in memory: {str(e)}")

        return current_opinion

    def _create_opinion_prompt(
        self,
        topic: str,
        analysis_result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Create prompt for opinion formation."""
        return f"""
        Based on the following analysis of {topic}, form a clear opinion:
        
        Analysis Results:
        {analysis_result.get('analysis_summary', '')}
        
        Market Context:
        {json.dumps(context, indent=2)}
        
        Consider:
        1. Strength of evidence in the analysis
        2. Market conditions and context
        3. Historical patterns and precedents
        4. Risk factors and uncertainties
        
        Provide a clear, well-reasoned opinion about {topic} that includes:
        1. Main belief/conclusion
        2. Key supporting evidence
        3. Potential counter-arguments
        4. Level of conviction
        """

    def _calculate_confidence(self, analysis_result: Dict[str, Any]) -> float:
        """Calculate initial confidence based on analysis results."""
        # Start with base confidence
        confidence = 0.5

        # Adjust based on analysis factors
        if "confidence" in analysis_result:
            confidence = analysis_result["confidence"]
        
        # Adjust based on data quality
        if analysis_result.get("data_quality_score"):
            confidence *= analysis_result["data_quality_score"]

        # Cap confidence
        return min(max(confidence, 0.0), 1.0)

    def _recalculate_confidence(
        self,
        current_confidence: float,
        validation_count: int,
        new_evidence: List[Dict[str, Any]]
    ) -> float:
        """Recalculate confidence based on new evidence."""
        # Start with current confidence
        confidence = current_confidence

        # Adjust based on validation history
        confidence *= (1.0 + (validation_count - 1) * 0.1)  # Increase with validations

        # Adjust based on new evidence
        for evidence in new_evidence:
            if evidence.get("matches_belief", False):
                confidence *= 1.1  # Increase confidence for supporting evidence
            else:
                confidence *= 0.9  # Decrease confidence for contradicting evidence

        # Cap confidence
        return min(max(confidence, 0.0), 1.0)
