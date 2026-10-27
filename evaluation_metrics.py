"""
Evaluation Metrics for OCR: WER (Word Error Rate) and CER (Character Error Rate)
"""

import difflib
import re
from typing import Tuple, List, Dict

class OCREvaluationMetrics:
    """Calculate WER and CER for OCR evaluation"""
    
    def __init__(self):
        pass
    
    def calculate_wer(self, reference: str, hypothesis: str) -> Tuple[float, Dict]:
        """
        Calculate Word Error Rate (WER)
        WER = (S + D + I) / N
        Where: S = substitutions, D = deletions, I = insertions, N = total words in reference
        """
        # Preprocess text
        ref_words = self.preprocess_text_for_words(reference)
        hyp_words = self.preprocess_text_for_words(hypothesis)
        
        # Calculate edit distance at word level
        edit_ops = self.calculate_edit_operations(ref_words, hyp_words)
        
        # Count operations
        substitutions = edit_ops['substitutions']
        deletions = edit_ops['deletions']
        insertions = edit_ops['insertions']
        
        # Calculate WER
        total_words = len(ref_words)
        if total_words == 0:
            wer = 0.0 if len(hyp_words) == 0 else float('inf')
        else:
            wer = (substitutions + deletions + insertions) / total_words
        
        return wer, {
            'substitutions': substitutions,
            'deletions': deletions,
            'insertions': insertions,
            'total_words': total_words,
            'correct_words': total_words - substitutions - deletions,
            'wer_percentage': wer * 100
        }
    
    def calculate_cer(self, reference: str, hypothesis: str) -> Tuple[float, Dict]:
        """
        Calculate Character Error Rate (CER)
        CER = (S + D + I) / N
        Where: S = substitutions, D = deletions, I = insertions, N = total characters in reference
        """
        # Preprocess text (remove extra spaces but keep structure)
        ref_chars = list(reference.strip())
        hyp_chars = list(hypothesis.strip())
        
        # Calculate edit distance at character level
        edit_ops = self.calculate_edit_operations(ref_chars, hyp_chars)
        
        # Count operations
        substitutions = edit_ops['substitutions']
        deletions = edit_ops['deletions']
        insertions = edit_ops['insertions']
        
        # Calculate CER
        total_chars = len(ref_chars)
        if total_chars == 0:
            cer = 0.0 if len(hyp_chars) == 0 else float('inf')
        else:
            cer = (substitutions + deletions + insertions) / total_chars
        
        return cer, {
            'substitutions': substitutions,
            'deletions': deletions,
            'insertions': insertions,
            'total_chars': total_chars,
            'correct_chars': total_chars - substitutions - deletions,
            'cer_percentage': cer * 100
        }
    
    def preprocess_text_for_words(self, text: str) -> List[str]:
        """Preprocess text for word-level analysis"""
        # Remove extra whitespace and split into words
        # Handle multiple languages including Hindi
        text = re.sub(r'\s+', ' ', text.strip())
        words = text.split()
        return words
    
    def calculate_edit_operations(self, seq1: List, seq2: List) -> Dict:
        """Calculate edit operations using dynamic programming"""
        m, n = len(seq1), len(seq2)
        
        # Create DP table
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        # Initialize base cases
        for i in range(m + 1):
            dp[i][0] = i  # deletions
        for j in range(n + 1):
            dp[0][j] = j  # insertions
        
        # Fill DP table
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i-1] == seq2[j-1]:
                    dp[i][j] = dp[i-1][j-1]  # match
                else:
                    dp[i][j] = 1 + min(
                        dp[i-1][j],     # deletion
                        dp[i][j-1],     # insertion
                        dp[i-1][j-1]    # substitution
                    )
        
        # Backtrack to count operations
        i, j = m, n
        substitutions = deletions = insertions = 0
        
        while i > 0 or j > 0:
            if i > 0 and j > 0 and seq1[i-1] == seq2[j-1]:
                i -= 1
                j -= 1
            elif i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + 1:
                substitutions += 1
                i -= 1
                j -= 1
            elif i > 0 and dp[i][j] == dp[i-1][j] + 1:
                deletions += 1
                i -= 1
            else:
                insertions += 1
                j -= 1
        
        return {
            'substitutions': substitutions,
            'deletions': deletions,
            'insertions': insertions,
            'total_edit_distance': dp[m][n]
        }
    
    def create_text_comparison_view(self, reference: str, hypothesis: str) -> str:
        """Create a visual comparison of reference and hypothesis text"""
        ref_words = self.preprocess_text_for_words(reference)
        hyp_words = self.preprocess_text_for_words(hypothesis)
        
        # Use difflib for visualization
        diff = list(difflib.unified_diff(ref_words, hyp_words, lineterm='', n=0))
        
        comparison_html = "<div style='font-family: monospace; background: #f8f9fa; padding: 10px; border-radius: 5px;'>"
        comparison_html += "<strong>Text Comparison:</strong><br><br>"
        
        # Create side-by-side comparison
        comparison_html += "<div style='display: flex; gap: 20px;'>"
        
        # Reference text
        comparison_html += "<div style='flex: 1;'>"
        comparison_html += "<strong style='color: #28a745;'>Reference Text:</strong><br>"
        comparison_html += f"<div style='background: #d4edda; padding: 8px; border-radius: 3px;'>{reference}</div>"
        comparison_html += "</div>"
        
        # Hypothesis text
        comparison_html += "<div style='flex: 1;'>"
        comparison_html += "<strong style='color: #dc3545;'>Extracted Text:</strong><br>"
        comparison_html += f"<div style='background: #f8d7da; padding: 8px; border-radius: 3px;'>{hypothesis}</div>"
        comparison_html += "</div>"
        
        comparison_html += "</div></div>"
        
        return comparison_html

if __name__ == "__main__":
    # Test the evaluation metrics
    evaluator = OCREvaluationMetrics()
    
    # Example usage
    reference = "हर घर जल जल जीवन मिशन"
    hypothesis = "हर घर जल जीवन मिशन"
    
    wer, wer_details = evaluator.calculate_wer(reference, hypothesis)
    cer, cer_details = evaluator.calculate_cer(reference, hypothesis)
    
    print(f"WER: {wer:.2%}")
    print(f"CER: {cer:.2%}")
    print(f"WER Details: {wer_details}")
    print(f"CER Details: {cer_details}")