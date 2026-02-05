"""Enhanced intent classification service.

This module provides an enhanced intent classification service that combines multiple approaches:
1. Keyword matching (optimized with tf-idf and n-gram)
2. Vector retrieval (topk similarity matching)
3. LLM-based intent recognition

The service uses a hybrid approach with RRF (Reciprocal Rank Fusion) to combine results
from keyword matching and vector retrieval. If the confidence score is above 0.8,
it directly adopts the result. Otherwise, it uses an LLM to make the final decision.

Example:
    from app.services.enhanced_intent_service import EnhancedIntentService
    
    service = EnhancedIntentService()
    result = service.classify_intent("帮我写个Python脚本")
    print(result)  # Output: {"intent": "code", "confidence": 0.95, "method": "hybrid"}
"""

import math
import re
from typing import Dict, List, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.config import settings
from app.utils.telemetry import get_tracer
from app.utils.math import cosine_similarity as calc_cosine_similarity
from app.services.monitoring_service import MonitoringService
from app.services.model_service import ModelService

from app.repositories.memory_repository import MemoryRepository
from app.services.cache_service import CacheService

# Get OpenTelemetry tracer
tracer = get_tracer()


class EnhancedIntentService:
    """Enhanced intent classification service.
    
    This service combines multiple approaches for intent classification:
    - Keyword matching with tf-idf and n-gram
    - Vector retrieval
    - LLM-based intent recognition
    
    Attributes:
        intent_keywords: A dictionary mapping intent categories to lists of keywords
        tfidf_vectorizer: TF-IDF vectorizer for keyword matching
        intent_embeddings: Precomputed embeddings for intent categories
        monitoring_service: Monitoring service for recording usage
    """

    def __init__(self):
        """Initialize the enhanced intent service.
        
        The service is initialized with intent keywords from settings and
        prepares the necessary components for intent classification.
        """
        # Load intent keywords from settings
        self.intent_keywords = settings.intent_keywords
        
        # Initialize TF-IDF vectorizer with n-gram support
        self.tfidf_vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),  # Support both unigrams and bigrams
            token_pattern=r'\b\w+\b',
            lowercase=True
        )
        
        # Prepare training data for TF-IDF
        self._prepare_tfidf_data()
        
        # Initialize monitoring service
        self.monitoring_service = MonitoringService()
        
        # Initialize model service for LLM-based intent recognition
        self.repository = MemoryRepository()
        self.model_service = ModelService(self.repository)
        
        # Initialize cache service for text embedding generation
        self.cache_service = CacheService(self.repository)
        
        # Prepare vector embeddings
        self.intent_embeddings = self._prepare_intent_embeddings()

    def _prepare_tfidf_data(self):
        """Prepare training data for TF-IDF vectorization.
        
        This method prepares the training data by creating synthetic documents
        for each intent category based on their keywords.
        """
        # Create synthetic documents for each intent
        documents = []
        self.intent_labels = []
        
        for intent, keywords in self.intent_keywords.items():
            # Create a document by joining all keywords for this intent
            document = ' '.join(keywords)
            documents.append(document)
            self.intent_labels.append(intent)
        
        # Fit the TF-IDF vectorizer
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(documents)

    def _prepare_intent_embeddings(self):
        """Prepare intent embeddings for vector retrieval.
        
        This method generates embeddings for each intent category using the cache service's
        embed_text method, which currently uses a deterministic hashing approach but
        can be replaced with a real embedding model in the future.
        
        Returns:
            A dictionary mapping intent categories to their embeddings
        """
        embeddings = {}
        for intent in self.intent_keywords:
            # Create a representative text for this intent using its keywords
            intent_text = ' '.join(self.intent_keywords[intent])
            # Generate embedding for the intent text
            embedding = self.cache_service.embed_text(intent_text)
            embeddings[intent] = embedding
        return embeddings

    def _keyword_match(self, query: str) -> List[Tuple[str, float]]:
        """Perform keyword matching using TF-IDF and n-gram optimization.
        
        Args:
            query: The user's query string
            
        Returns:
            A list of tuples (intent, score) sorted by score in descending order
        """
        # Step 1: Transform the query using the TF-IDF vectorizer
        query_vector = self.tfidf_vectorizer.transform([query])
        
        # Step 2: Calculate cosine similarity between the query vector and intent vectors
        similarities = []
        for i, intent in enumerate(self.intent_labels):
            # Get the TF-IDF vector for this intent
            intent_vector = self.tfidf_matrix[i]
            # Calculate cosine similarity
            if query_vector.nnz > 0 and intent_vector.nnz > 0:
                similarity = cosine_similarity(query_vector, intent_vector)[0][0]
            else:
                similarity = 0.0
            similarities.append((intent, similarity))
        
        # Step 3: Also perform simple keyword counting as fallback
        # This helps with cases where TF-IDF might not capture exact keyword matches
        query_lower = query.lower()
        keyword_counts = {}
        for intent, keywords in self.intent_keywords.items():
            count = sum(1 for keyword in keywords if keyword.lower() in query_lower)
            keyword_counts[intent] = count / len(keywords) if keywords else 0.0
        
        # Step 4: Combine TF-IDF similarity with keyword count
        combined_scores = []
        for intent, tfidf_score in similarities:
            keyword_score = keyword_counts.get(intent, 0.0)
            # Weighted combination
            combined_score = 0.6 * tfidf_score + 0.4 * keyword_score
            combined_scores.append((intent, combined_score))
        
        # Step 5: Sort by combined score in descending order
        combined_scores.sort(key=lambda x: x[1], reverse=True)
        
        return combined_scores

    def _vector_retrieval(self, query: str, topk: int = 3) -> List[Tuple[str, float]]:
        """Perform vector retrieval for intent matching.
        
        Args:
            query: The user's query string
            topk: Number of top results to return
            
        Returns:
            A list of tuples (intent, score) sorted by score in descending order
        """
        # Step 1: Generate an embedding for the query
        query_embedding = self.cache_service.embed_text(query)
        
        # Step 2: Calculate similarity between query embedding and intent embeddings
        similarities = []
        for intent, embedding in self.intent_embeddings.items():
            # Calculate cosine similarity
            similarity = calc_cosine_similarity(query_embedding, embedding)
            # Add a small boost for exact keyword matches
            query_lower = query.lower()
            intent_keywords = self.intent_keywords.get(intent, [])
            exact_matches = sum(1 for keyword in intent_keywords if keyword.lower() in query_lower)
            if exact_matches > 0:
                similarity += 0.1 * exact_matches
            similarities.append((intent, similarity))
        
        # Step 3: Sort by similarity and return topk
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:topk]

    def _rrf_fusion(self, keyword_results: List[Tuple[str, float]], 
                   vector_results: List[Tuple[str, float]], 
                   k: int = 60) -> List[Tuple[str, float]]:
        """Perform Reciprocal Rank Fusion (RRF) to combine results.
        
        Args:
            keyword_results: Results from keyword matching
            vector_results: Results from vector retrieval
            k: RRF parameter (typically 60)
            
        Returns:
            A list of tuples (intent, score) sorted by score in descending order
        """
        # Create a dictionary to store fused scores
        fused_scores = {}
        
        # Process keyword results
        for rank, (intent, score) in enumerate(keyword_results):
            if intent not in fused_scores:
                fused_scores[intent] = 0
            # Use only rank-based score for RRF
            fused_scores[intent] += 1 / (rank + k)
        
        # Process vector results
        for rank, (intent, score) in enumerate(vector_results):
            if intent not in fused_scores:
                fused_scores[intent] = 0
            # Use only rank-based score for RRF
            fused_scores[intent] += 1 / (rank + k)
        
        # Convert to list and sort
        fused_results = sorted(fused_scores.items(), 
                             key=lambda x: x[1], 
                             reverse=True)
        
        return fused_results

    def _llm_intent_recognition(self, query: str, 
                               keyword_results: List[Tuple[str, float]], 
                               vector_results: List[Tuple[str, float]]) -> Tuple[str, float]:
        """Use LLM for intent recognition as a fallback.
        
        Args:
            query: The user's query string
            keyword_results: Results from keyword matching
            vector_results: Results from vector retrieval
            
        Returns:
            A tuple (intent, confidence) with the LLM's prediction
        """
        try:
            # Step 1: Construct the prompt for intent recognition
            prompt = self._construct_intent_prompt(query, keyword_results, vector_results)
            
            # Step 2: Mock LLM response for demonstration
            # In a real system, this would make an actual API call to a language model
            # For now, we'll return a mock response based on the fused results
            fused_results = self._rrf_fusion(keyword_results, vector_results)
            
            if fused_results:
                # Get the top intent from fused results
                top_intent, top_score = fused_results[0]
                # Adjust confidence slightly to simulate LLM reasoning
                confidence = min(top_score * 1.1, 1.0)
                return top_intent, confidence
            else:
                return "general", 0.5
                
        except Exception as e:
            # If there's an error, fall back to fused results
            print(f"Error in LLM intent recognition: {str(e)}")
            fused_results = self._rrf_fusion(keyword_results, vector_results)
            if fused_results:
                return fused_results[0]
            else:
                return "general", 0.5
    
    def _parse_llm_response(self, response: str) -> Optional[Tuple[str, float]]:
        """Parse the LLM response to extract intent and confidence.
        
        Args:
            response: The LLM's response text
            
        Returns:
            A tuple (intent, confidence) if parsing is successful, None otherwise
        """
        try:
            # Look for intent in the response
            intent_match = re.search(r'INTENT:\s*(\w+)', response, re.IGNORECASE)
            confidence_match = re.search(r'CONFIDENCE:\s*(\d+\.\d+)', response, re.IGNORECASE)
            
            if intent_match and confidence_match:
                intent = intent_match.group(1).lower()
                confidence = float(confidence_match.group(1))
                
                # Validate intent and confidence
                if intent in self.intent_keywords and 0.0 <= confidence <= 1.0:
                    return intent, confidence
            
            # If parsing fails, return None
            return None
            
        except Exception as e:
            print(f"Error parsing LLM response: {str(e)}")
            return None
    
    def _construct_intent_prompt(self, query: str, 
                               keyword_results: List[Tuple[str, float]], 
                               vector_results: List[Tuple[str, float]]) -> str:
        """Construct a prompt for LLM-based intent recognition.
        
        Args:
            query: The user's query string
            keyword_results: Results from keyword matching
            vector_results: Results from vector retrieval
            
        Returns:
            A formatted prompt for the LLM
        """
        # Get intent categories
        intent_categories = list(self.intent_keywords.keys())
        
        # Format keyword results
        formatted_keyword_results = "\n".join([f"- {intent}: {score:.2f}" for intent, score in keyword_results[:3]])
        
        # Format vector results
        formatted_vector_results = "\n".join([f"- {intent}: {score:.2f}" for intent, score in vector_results[:3]])
        
        prompt = f"""You are an intent classification assistant. Your task is to determine the most appropriate intent category for the given user query based on the provided context.

User Query:
{query}

Intent Categories:
{', '.join(intent_categories)}

Keyword Matching Results:
{formatted_keyword_results}

Vector Retrieval Results:
{formatted_vector_results}

Instructions:
1. Analyze the user query carefully
2. Consider the results from keyword matching and vector retrieval
3. Determine the most appropriate intent category
4. Provide your answer in the format: INTENT: [category]\nCONFIDENCE: [score]
5. The confidence score should be a value between 0.0 and 1.0
6. Base your decision primarily on the user query, using the matching results as supporting evidence

Example Output:
INTENT: code
CONFIDENCE: 0.95
"""
        
        return prompt

    def classify_intent(self, query: str) -> Dict[str, any]:
        """Classify a user query into an intent category using a hybrid approach.
        
        Args:
            query: The user's query string
            
        Returns:
            A dictionary with the following keys:
            - intent: The classified intent category
            - confidence: Confidence score (0-1)
            - method: Method used for classification ("hybrid", "llm")
            - details: Additional details about the classification process
        """
        with tracer.start_as_current_span("classify_intent", attributes={
            "query": query[:50]  # Truncate for span attributes
        }) as span:
            # Step 1: Perform keyword matching
            keyword_results = self._keyword_match(query)
            
            # Step 2: Check if keyword match scores are all very low
            # If all keyword match scores are below 0.05, it's likely a general intent
            max_keyword_score = keyword_results[0][1] if keyword_results else 0.0
            if max_keyword_score < 0.05:
                # All keyword match scores are very low, should be general intent
                intent = "general"
                confidence = 0.5
                method = "hybrid"
                
                # Set span attributes
                span.set_attribute("intent", intent)
                span.set_attribute("confidence", confidence)
                span.set_attribute("method", method)
                span.set_attribute("threshold_met", True)
                
                # Record usage
                self.monitoring_service.record_model_usage(
                    model_id="intent-classification-hybrid",
                    user_id="system",
                    request_time=0.0,
                    response_time=0.0,
                    tokens_used=0,
                    status="success"
                )
                
                return {
                    "intent": intent,
                    "confidence": confidence,
                    "method": method,
                    "details": {
                        "keyword_results": keyword_results,
                        "vector_results": [],
                        "fused_results": [],
                        "normalized_fused_results": []
                    }
                }
            
            # Step 3: Perform vector retrieval
            vector_results = self._vector_retrieval(query)
            
            # Step 4: Perform RRF fusion
            fused_results = self._rrf_fusion(keyword_results, vector_results)
            
            # Normalize fused scores to 0-1 range for confidence thresholding
            normalized_fused_results = []
            if fused_results:
                max_score = fused_results[0][1]
                if max_score > 0:
                    normalized_fused_results = [(intent, score / max_score) 
                                             for intent, score in fused_results]
                else:
                    normalized_fused_results = [(intent, 0.0) for intent, score in fused_results]
            
            # Step 5: Check confidence threshold
            if normalized_fused_results and normalized_fused_results[0][1] >= 0.8:
                # Confidence is high enough, use hybrid result
                intent, confidence = normalized_fused_results[0]
                method = "hybrid"
                
                # Set span attributes
                span.set_attribute("intent", intent)
                span.set_attribute("confidence", confidence)
                span.set_attribute("method", method)
                span.set_attribute("threshold_met", True)
                
                # Record usage
                self.monitoring_service.record_model_usage(
                    model_id="intent-classification-hybrid",
                    user_id="system",
                    request_time=0.0,
                    response_time=0.0,
                    tokens_used=0,
                    status="success"
                )
                
                return {
                    "intent": intent,
                    "confidence": confidence,
                    "method": method,
                    "details": {
                        "keyword_results": keyword_results,
                        "vector_results": vector_results,
                        "fused_results": fused_results,
                        "normalized_fused_results": normalized_fused_results
                    }
                }
            else:
                # Confidence is not high enough, use LLM
                intent, confidence = self._llm_intent_recognition(
                    query, keyword_results, vector_results
                )
                method = "llm"
                
                # Set span attributes
                span.set_attribute("intent", intent)
                span.set_attribute("confidence", confidence)
                span.set_attribute("method", method)
                span.set_attribute("threshold_met", False)
                
                # Record usage
                self.monitoring_service.record_model_usage(
                    model_id="intent-classification-llm",
                    user_id="system",
                    request_time=0.0,
                    response_time=0.0,
                    tokens_used=100,  # Estimated tokens
                    status="success"
                )
                
                return {
                    "intent": intent,
                    "confidence": confidence,
                    "method": method,
                    "details": {
                        "keyword_results": keyword_results,
                        "vector_results": vector_results,
                        "fused_results": fused_results,
                        "normalized_fused_results": normalized_fused_results
                    }
                }
