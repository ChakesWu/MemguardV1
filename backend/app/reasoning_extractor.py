"""
Decision Reasoning Extractor

Extracts structured reasoning from LLM outputs using pattern matching
and keyword detection.
"""

import re
from typing import Dict, Optional, List


class ReasoningExtractor:
    """Extract decision reasoning from LLM outputs"""

    # Common decision patterns
    DECISION_PATTERNS = {
        "file_sar": r"(?i)(file|submit|recommend|require).*?(sar|suspicious activity report)",
        "clear": r"(?i)(clear|no action|dismiss|not suspicious|no evidence)",
        "escalate": r"(?i)(escalate|review|investigate|require.*?review|manual review)",
        "approve": r"(?i)(approve|accept|confirm|proceed)",
        "reject": r"(?i)(reject|decline|deny|refuse)",
    }

    # Reasoning keywords that indicate explanatory content
    REASONING_KEYWORDS = [
        "because", "due to", "based on", "given that", "considering",
        "since", "as", "reason", "violates", "matches", "indicates",
        "suggests", "shows", "demonstrates", "evidenced by", "therefore",
        "thus", "consequently", "as a result", "resulting from"
    ]

    @staticmethod
    def extract_decision_type(llm_output: str) -> str:
        """
        Extract decision type from LLM output

        Args:
            llm_output: Raw LLM response text

        Returns:
            Decision type string (file_sar, clear, escalate, etc.)
        """
        if not llm_output:
            return "unknown"

        output_lower = llm_output.lower()

        # Check each pattern
        for decision_type, pattern in ReasoningExtractor.DECISION_PATTERNS.items():
            if re.search(pattern, output_lower):
                return decision_type

        return "unknown"

    @staticmethod
    def extract_reasoning(llm_output: str, max_length: int = 500) -> str:
        """
        Extract reasoning sentences from LLM output

        Looks for sentences that contain reasoning keywords and constructs
        a coherent explanation of why the decision was made.

        Args:
            llm_output: Raw LLM response text
            max_length: Max reasoning text length

        Returns:
            Extracted reasoning text
        """
        if not llm_output:
            return "No output provided"

        # Split into sentences
        sentences = re.split(r'[.!?]\s+', llm_output)
        reasoning_sentences = []

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Check if sentence contains reasoning keywords
            if any(keyword in sentence.lower() for keyword in ReasoningExtractor.REASONING_KEYWORDS):
                reasoning_sentences.append(sentence)

        # If no reasoning keywords found, try to extract key information
        if not reasoning_sentences:
            # Look for sentences with important indicators
            for sentence in sentences:
                sentence = sentence.strip()
                if any(word in sentence.lower() for word in ["risk", "threshold", "pattern", "violation", "suspicious"]):
                    reasoning_sentences.append(sentence)

        # Join and truncate
        if reasoning_sentences:
            reasoning = ". ".join(reasoning_sentences)
            if len(reasoning) > max_length:
                reasoning = reasoning[:max_length] + "..."
            return reasoning
        else:
            # Fallback: return first few sentences
            fallback = ". ".join(sentences[:3])
            if len(fallback) > max_length:
                fallback = fallback[:max_length] + "..."
            return fallback or "No explicit reasoning found in output."

    @staticmethod
    def extract_confidence(llm_output: str) -> float:
        """
        Extract confidence score from LLM output

        Looks for patterns like:
        - "confidence: 0.92"
        - "92% confident"
        - "high confidence" (maps to 0.85)

        Args:
            llm_output: Raw LLM response text

        Returns:
            Confidence score (0-1)
        """
        if not llm_output:
            return 0.75  # Default

        output_lower = llm_output.lower()

        # Look for numeric confidence (e.g., "confidence: 0.92")
        numeric_match = re.search(r'confidence[:\s]+([0-9.]+)', output_lower)
        if numeric_match:
            try:
                score = float(numeric_match.group(1))
                # If > 1, assume it's percentage
                if score > 1:
                    score = score / 100.0
                return round(min(max(score, 0.0), 1.0), 2)
            except ValueError:
                pass

        # Look for percentage (e.g., "92% confident")
        percent_match = re.search(r'([0-9]+)%\s*confident', output_lower)
        if percent_match:
            try:
                score = float(percent_match.group(1)) / 100.0
                return round(score, 2)
            except ValueError:
                pass

        # Look for qualitative confidence
        if any(word in output_lower for word in ["high confidence", "very confident", "certain", "definite"]):
            return 0.85
        elif any(word in output_lower for word in ["medium confidence", "moderately confident", "probable"]):
            return 0.65
        elif any(word in output_lower for word in ["low confidence", "uncertain", "unclear", "possible"]):
            return 0.45

        # Default confidence
        return 0.75

    @staticmethod
    def extract_risk_score(llm_output: str) -> Optional[float]:
        """
        Extract risk score from LLM output

        Looks for patterns like:
        - "risk score: 0.89"
        - "risk: 89%"
        - "0.89 risk"

        Args:
            llm_output: Raw LLM response text

        Returns:
            Risk score (0-1) or None
        """
        if not llm_output:
            return None

        output_lower = llm_output.lower()

        # Look for "risk score: X"
        risk_match = re.search(r'risk\s*score[:\s]+([0-9.]+)', output_lower)
        if risk_match:
            try:
                score = float(risk_match.group(1))
                if score > 1:
                    score = score / 100.0
                return round(min(max(score, 0.0), 1.0), 2)
            except ValueError:
                pass

        # Look for "risk: X%"
        percent_match = re.search(r'risk[:\s]+([0-9]+)%', output_lower)
        if percent_match:
            try:
                score = float(percent_match.group(1)) / 100.0
                return round(score, 2)
            except ValueError:
                pass

        return None

    @staticmethod
    def extract_key_factors(llm_output: str, max_factors: int = 5) -> List[str]:
        """
        Extract key decision factors from LLM output

        Looks for bullet points or numbered lists.

        Args:
            llm_output: Raw LLM response text
            max_factors: Maximum number of factors to extract

        Returns:
            List of key factors
        """
        if not llm_output:
            return []

        factors = []

        # Look for bullet points
        bullet_matches = re.findall(r'[•\-\*]\s*([^\n]+)', llm_output)
        factors.extend([f.strip() for f in bullet_matches if f.strip()])

        # Look for numbered lists
        numbered_matches = re.findall(r'\d+\.\s*([^\n]+)', llm_output)
        factors.extend([f.strip() for f in numbered_matches if f.strip()])

        # Deduplicate and limit
        unique_factors = []
        seen = set()
        for factor in factors:
            if factor.lower() not in seen and len(unique_factors) < max_factors:
                unique_factors.append(factor)
                seen.add(factor.lower())

        return unique_factors

    @staticmethod
    def extract_full_reasoning(llm_output: str) -> Dict:
        """
        Extract full reasoning structure from LLM output

        Returns:
            Dict with decision_type, reasoning, confidence, risk_score, key_factors
        """
        return {
            "decision_type": ReasoningExtractor.extract_decision_type(llm_output),
            "reasoning": ReasoningExtractor.extract_reasoning(llm_output),
            "confidence": ReasoningExtractor.extract_confidence(llm_output),
            "risk_score": ReasoningExtractor.extract_risk_score(llm_output),
            "key_factors": ReasoningExtractor.extract_key_factors(llm_output),
        }
