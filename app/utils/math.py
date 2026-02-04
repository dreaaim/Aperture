"""Math utility functions.

This module provides utility functions for mathematical operations, including:
- Cosine similarity calculation for vector comparison

These functions are used throughout the application for tasks like:
- Comparing text embeddings in the cache service
- Calculating similarity scores for cached entries

Example:
    from app.utils.math import cosine_similarity
    
    # Calculate cosine similarity between two vectors
    vector1 = [1.0, 2.0, 3.0]
    vector2 = [1.0, 2.0, 3.0]
    similarity = cosine_similarity(vector1, vector2)
    print(similarity)  # Output: 1.0 (identical vectors)
    
    vector3 = [1.0, 2.0, 3.0]
    vector4 = [-1.0, -2.0, -3.0]
    similarity = cosine_similarity(vector3, vector4)
    print(similarity)  # Output: -1.0 (opposite vectors)
    
    vector5 = [1.0, 0.0, 0.0]
    vector6 = [0.0, 1.0, 0.0]
    similarity = cosine_similarity(vector5, vector6)
    print(similarity)  # Output: 0.0 (orthogonal vectors)
"""

import math
from typing import List

def cosine_similarity(vector_a: List[float], vector_b: List[float]) -> float:
    """Compute cosine similarity between two vectors.
    
    Cosine similarity measures the similarity between two non-zero vectors
    by calculating the cosine of the angle between them. It ranges from -1 to 1:
    - 1: Vectors are identical
    0: Vectors are orthogonal (no similarity)
    -1: Vectors are opposite
    
    Args:
        vector_a: First vector as a list of floats
        vector_b: Second vector as a list of floats
        
    Returns:
        The cosine similarity score between the two vectors
        
    Example:
        >>> from app.utils.math import cosine_similarity
        >>> vector1 = [0.1, 0.2, 0.3]
        >>> vector2 = [0.1, 0.2, 0.3]
        >>> cosine_similarity(vector1, vector2)
        1.0
        
        >>> vector3 = [0.1, 0.2, 0.3]
        >>> vector4 = [0.4, 0.5, 0.6]
        >>> cosine_similarity(vector3, vector4)
        0.9746318461970762  # Example value
    """
    # Calculate the dot product of the two vectors
    # The dot product is the sum of the products of corresponding elements
    dot = sum(a * b for a, b in zip(vector_a, vector_b))
    
    # Calculate the Euclidean norm (magnitude) of each vector
    # The norm is the square root of the sum of squared elements
    norm_a = math.sqrt(sum(a * a for a in vector_a))
    norm_b = math.sqrt(sum(b * b for b in vector_b))
    
    # Handle division by zero case
    # If either vector has zero magnitude, similarity is 0
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    # Calculate cosine similarity
    # Similarity = dot product / (norm of a * norm of b)
    return dot / (norm_a * norm_b)
