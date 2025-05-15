from datetime import datetime
from typing import Dict, Any, Optional, List
import asyncio
import logging
import numpy as np
# from textblob import TextBlob # Example: for simple sentiment scoring if not provided by news API
# import nltk # Example: for more advanced NLP tasks
# nltk.download('vader_lexicon') # if using NLTK VADER for sentiment
# from nltk.sentiment.vader import SentimentIntensityAnalyzer

from app.services.market_data_service import MarketDataService
from app.chaetra.llm import LLMManager # For summarizing or interpreting sentiment
from app.core.config import settings

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(
        self,
        market_data_service: MarketDataService,
        llm_manager: Optional[LLMManager] = None
    ):
        self.market_data_service = market_data_service
        self.llm_manager = llm_manager
        # self.vader_analyzer = SentimentIntensityAnalyzer() # Example if using NLTK VADER

    async def analyze_news_sentiment(
        self, 
        symbols: Optional[List[str]] = None, 
        topics: Optional[List[str]] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Fetches news and analyzes its sentiment.
        """
        news_items = await self.market_data_service.get_market_news(symbols=symbols, topics=topics, limit=limit)
        
        if not news_items:
            return {
                "overall_sentiment_score": 0.0, # Neutral
                "overall_sentiment_label": "neutral",
                "confidence": 0.5,
                "articles_analyzed": 0,
                "sentiment_breakdown": {}, # e.g., positive, negative, neutral counts
                "key_themes": [],
                "detailed_articles": []
            }

        analyzed_articles = []
        sentiment_scores = []

        for item in news_items:
            title = item.get('title', '')
            summary = item.get('summary', '')
            text_to_analyze = f"{title}. {summary}" if summary else title

            # Priority 1: Use sentiment score from data provider if available (e.g., Alpha Vantage)
            article_sentiment_score = item.get('overall_sentiment_score')
            article_sentiment_label = item.get('overall_sentiment_label')
            
            # Priority 2: Use LLM for sentiment if available and no provider score
            if article_sentiment_score is None and self.llm_manager:
                try:
                    # This prompt could be more sophisticated
                    sentiment_prompt = f"Analyze the sentiment of the following news headline and summary. Classify it as 'positive', 'negative', or 'neutral' and provide a confidence score (0.0 to 1.0).\n\nText: \"{text_to_analyze}\"\n\nOutput JSON: {{\"sentiment_label\": \"str\", \"sentiment_score\": float (negative: -1 to 0, neutral: 0, positive: 0 to 1)}}"
                    llm_response = await self.llm_manager.generate_structured_output(
                        sentiment_prompt, 
                        {"sentiment_label": "str", "sentiment_score": "float"}
                    )
                    article_sentiment_label = llm_response.get("sentiment_label", "neutral")
                    article_sentiment_score = llm_response.get("sentiment_score", 0.0)
                except Exception as e:
                    logger.error(f"LLM sentiment analysis failed for article '{title}': {e}")
                    # Fallback to simpler method if LLM fails

            # Priority 3: (Placeholder) Simple NLP if no provider/LLM score (e.g., TextBlob or VADER)
            # if article_sentiment_score is None:
            #     # blob = TextBlob(text_to_analyze)
            #     # article_sentiment_score = blob.sentiment.polarity # Ranges from -1 to 1
            #     # if article_sentiment_score > 0.1: article_sentiment_label = "positive"
            #     # elif article_sentiment_score < -0.1: article_sentiment_label = "negative"
            #     # else: article_sentiment_label = "neutral"
            #     pass # Keep as None if no simple NLP implemented

            if article_sentiment_score is not None: # Only include if a score was determined
                sentiment_scores.append(article_sentiment_score)
                analyzed_articles.append({
                    **item,
                    "analyzed_sentiment_score": article_sentiment_score,
                    "analyzed_sentiment_label": article_sentiment_label
                })
        
        overall_score = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
        overall_label = "neutral"
        if overall_score > settings.SENTIMENT_POSITIVE_THRESHOLD: # e.g., 0.15
            overall_label = "positive"
        elif overall_score < settings.SENTIMENT_NEGATIVE_THRESHOLD: # e.g., -0.15
            overall_label = "negative"

        # Placeholder for key theme extraction (could use LLM or NLP topic modeling)
        key_themes = []
        # if self.llm_manager and analyzed_articles:
        #     all_titles = ". ".join([art['title'] for art in analyzed_articles[:10]]) # Summarize first 10 titles
        #     themes_prompt = f"Extract up to 5 key themes or topics from these news headlines: \"{all_titles}\". Output JSON: {{\"themes\": List[str]}}"
        #     try:
        #         theme_response = await self.llm_manager.generate_structured_output(themes_prompt, {"themes": "List[str]"})
        #         key_themes = theme_response.get("themes", [])
        #     except Exception as e:
        #         logger.error(f"LLM theme extraction failed: {e}")


        return {
            "overall_sentiment_score": round(overall_score, 3),
            "overall_sentiment_label": overall_label,
            "confidence": round(np.std(sentiment_scores) if len(sentiment_scores) > 1 else 0.5, 2), # Simplified confidence
            "articles_analyzed": len(analyzed_articles),
            "sentiment_breakdown": self._get_sentiment_breakdown(analyzed_articles),
            "key_themes": key_themes, # To be implemented
            "detailed_articles": analyzed_articles
        }

    def _get_sentiment_breakdown(self, analyzed_articles: List[Dict[str, Any]]) -> Dict[str, int]:
        breakdown = {"positive": 0, "negative": 0, "neutral": 0}
        for article in analyzed_articles:
            label = article.get("analyzed_sentiment_label", "neutral").lower()
            if "positive" in label: # Handle variations like "somewhat positive"
                breakdown["positive"] += 1
            elif "negative" in label:
                breakdown["negative"] += 1
            else:
                breakdown["neutral"] += 1
        return breakdown

    async def get_social_media_sentiment(self, query: str) -> Dict[str, Any]:
        """
        Placeholder for fetching and analyzing social media sentiment.
        Requires integration with social media APIs (Twitter, Reddit, etc.)
        """
        logger.warning("Social media sentiment analysis is not fully implemented yet.")
        # Example structure:
        # raw_posts = await self._fetch_social_media_posts(query, sources)
        # analyzed_posts = []
        # for post in raw_posts:
        #    sentiment = self._analyze_post_sentiment(post['text']) # Using VADER or LLM
        #    analyzed_posts.append({**post, **sentiment})
        # overall_social_sentiment = self._aggregate_social_sentiment(analyzed_posts)
        return {
            "query": query,
            "overall_sentiment_score": 0.0,
            "overall_sentiment_label": "neutral",
            "posts_analyzed": 0,
            "top_keywords": [],
            "error": "Not implemented"
        }

    async def get_combined_sentiment_report(
        self, 
        symbols: Optional[List[str]] = None, 
        topics: Optional[List[str]] = None,
        social_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Combines news and social media sentiment.
        """
        news_task = self.analyze_news_sentiment(symbols=symbols, topics=topics)
        social_task = self.get_social_media_sentiment(query=social_query if social_query else (symbols[0] if symbols else "market"))
        
        news_sentiment_result, social_sentiment_result = await asyncio.gather(news_task, social_task)
        
        # Combine scores (example: weighted average if both available)
        # This is a very basic combination logic.
        combined_score = news_sentiment_result.get("overall_sentiment_score", 0.0)
        if social_sentiment_result.get("posts_analyzed", 0) > 0:
            combined_score = (news_sentiment_result.get("overall_sentiment_score", 0.0) * 0.7) + \
                             (social_sentiment_result.get("overall_sentiment_score", 0.0) * 0.3)
        
        combined_label = "neutral"
        if combined_score > settings.SENTIMENT_POSITIVE_THRESHOLD: combined_label = "positive"
        elif combined_score < settings.SENTIMENT_NEGATIVE_THRESHOLD: combined_label = "negative"

        return {
            "overall_combined_score": round(combined_score, 3),
            "overall_combined_label": combined_label,
            "news_sentiment": news_sentiment_result,
            "social_sentiment": social_sentiment_result, # Will show "Not implemented" for now
            "report_generated_at": datetime.utcnow().isoformat()
        }

# Example usage:
# async def main():
#     from app.core.cache import RedisCache
#     from app.services.market_data_service import MarketDataService
#     cache = RedisCache()
#     md_service = MarketDataService(cache=cache)
#     # llm_mgr = LLMManager() # if using LLM
#     sentiment_analyzer = SentimentAnalyzer(market_data_service=md_service) #, llm_manager=llm_mgr)
    
#     report = await sentiment_analyzer.get_combined_sentiment_report(symbols=["AAPL"], social_query="Apple stock")
#     import json
#     print(json.dumps(report, indent=2, default=str))

# if __name__ == "__main__":
#     asyncio.run(main())
