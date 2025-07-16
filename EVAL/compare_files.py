import os
import re
from evaluate import load
class FIleComparator:
            
    def __init__(self, text1: str, text2: str):
        self.text1 = text1
        self.text2 = text2
        self.wer_evaluator = load("wer")
    
    def _calculate_wer(self, reference: str, hypothesis: str) -> float:
        """Calculate Word Error Rate."""
        return self.wer_evaluator.compute(predictions=[hypothesis], references=[reference])
    

    def _clean_text(self, text: str) -> str:
        """
        Clean text by removing unwanted characters and normalizing whitespace.
        This function is used to clean both the reference and hypothesis texts
        before calculating WER, CER, BERTScore, and METEOR scores.
        The cleaning process includes:
        - Removing unwanted characters (e.g., punctuation, special characters)
        - Normalizing whitespace
        - Removing extra spaces
        - Removing leading and trailing spaces
        - Normalizing to lowercase
        """
        # Remove unwanted characters (e.g., punctuation, special characters)
        text = re.sub(r'[^\w\s]', '', text)
        # Normalize whitespace
        text = ' '.join(text.split())
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text)
        # Remove leading and trailing spaces
        text = text.strip()
        # nomalize to lowercase
        text = text.lower()

        return text
    
    def print_wer_and_len(self):
        """
        Print the WER score between the two texts.
        """
        # Clean the texts before calculating WER
        cleaned_text1 = self._clean_text(self.text1)
        cleaned_text2 = self._clean_text(self.text2)
        cleaned_wer_score  = self._calculate_wer(cleaned_text2, cleaned_text1)
        print(f"WER score between the two texts: {cleaned_wer_score}")
        print(f"Length of text1: {len(cleaned_text1.split())}")
        print(f"Length of text2: {len(cleaned_text2.split())}")
        return cleaned_wer_score

if __name__ == "__main__":
    # Example usage
    text1_path = input("Enter the path to the first text file: ")
    text2_path = input("Enter the path to the second text file: ")
    with open(text1_path, 'r') as file:
        text1 = file.read()
    with open(text2_path, 'r') as file:
        text2 = file.read()
    # Create an instance of the FIleComparator class and print WER and lengths
    comparator = FIleComparator(text1, text2)
    comparator.print_wer_and_len()