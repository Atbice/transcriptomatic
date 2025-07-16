# ./EVAL/evaluation/evaluator.py
import os
import sys
from pathlib import Path

# Calculate the directory containing the EVAL package
SCRIPT_DIR = Path(__file__).resolve().parent
EVAL_DIR = SCRIPT_DIR.parent # This is /home/zeijlon/dev/transcriptomatic/EVAL
DIR_CONTAINING_EVAL = EVAL_DIR.parent # This is /home/zeijlon/dev/transcriptomatic (the project root)

# Add the directory containing EVAL to sys.path for robust imports
if str(DIR_CONTAINING_EVAL) not in sys.path:
    sys.path.insert(0, str(DIR_CONTAINING_EVAL))

# Recalculate PROJECT_ROOT based on the corrected DIR_CONTAINING_EVAL
PROJECT_ROOT = DIR_CONTAINING_EVAL

from datetime import datetime
import re
from evaluate import load
from bert_score import score
import Levenshtein
import nltk
from nltk.tokenize import word_tokenize
from nltk.translate.meteor_score import meteor_score
import stanza
from typing import Dict
import glob
import csv


from EVAL.evaluation.llm_eval import LLMEvaluator


# Initialize stanza for Swedish
stanza.download('sv')
nlp = stanza.Pipeline('sv', processors='tokenize', verbose=False)
# Initialize NLTK for tokenization
nltk.download('punkt_tab')
nltk.download('wordnet')

class Evaluator:
    def __init__(self):
        self.wer_evaluator = load("wer")
        self.llm_evaluator = LLMEvaluator() # Initialize LLMEvaluator

    def _preprocess_text(self, text: str) -> str:
        """Preprocess text by stripping and normalizing whitespace."""
        return ' '.join(re.split(r'\s+', text.strip()))

    def _calculate_wer(self, reference: str, hypothesis: str) -> float:
        """Calculate Word Error Rate."""
        return self.wer_evaluator.compute(predictions=[hypothesis], references=[reference])

    def _calculate_cer(self, reference: str, hypothesis: str) -> float:
        """Calculate Character Error Rate."""
        return Levenshtein.distance(reference, hypothesis) / max(len(reference), 1)

    def _calculate_bertscore(self, reference: str, hypothesis: str) -> float:
        """Calculate BERTScore F1."""
        reference_sents = [sent.text for sent in nlp(reference).sentences]
        hypothesis_sents = [sent.text for sent in nlp(hypothesis).sentences]
        min_len = min(len(reference_sents), len(hypothesis_sents))
        if min_len == 0:
            return 0.0
        reference_sents = reference_sents[:min_len]
        hypothesis_sents = hypothesis_sents[:min_len]
        _, _, F1 = score(
            hypothesis_sents,
            reference_sents,
            model_type='bert-base-multilingual-cased',
            lang='sv',
            verbose=False
        )
        return F1.mean().item()

    def _calculate_meteor(self, reference: str, hypothesis: str) -> float:
        """Calculate METEOR score."""
        ref_tokens = word_tokenize(reference, language='swedish')
        hyp_tokens = word_tokenize(hypothesis, language='swedish')
        return meteor_score([ref_tokens], hyp_tokens)

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

    def evaluate_transcription(
            self,
            model_name: str,
            audio_file_name: str,
            transcription_type: str,
            transcription: str,
            correct_transcription: str
        ) -> Dict:
        """Evaluate a pre-generated transcription against the correct transcription."""
        transcription = self._preprocess_text(transcription)
        correct_transcription = self._preprocess_text(correct_transcription)

        # Clean the transcriptions
        # Note: The cleaning process is applied to both the reference and hypothesis texts
        cleaned_transcription = self._clean_text(transcription)
        cleaned_correct_transcription = self._clean_text(correct_transcription)

        # Calculate evaluation metrics
        wer_score = self._calculate_wer(correct_transcription, transcription)
        cer_score = self._calculate_cer(correct_transcription, transcription)
        bertscore = self._calculate_bertscore(correct_transcription, transcription)
        meteor_score = self._calculate_meteor(correct_transcription, transcription)

        cleaned_wer_score  = self._calculate_wer(cleaned_correct_transcription, cleaned_transcription)
        cleaned_cer_score = self._calculate_cer(cleaned_correct_transcription, cleaned_transcription)
        cleaned_bertscore = self._calculate_bertscore(cleaned_correct_transcription, cleaned_transcription)
        cleaned_meteor_score = self._calculate_meteor(cleaned_correct_transcription, cleaned_transcription)

        eval_result = {
            "model": model_name,
            "audio_file": audio_file_name,
            "correct_transcription": correct_transcription,
            "WER_score": wer_score,
            "CER_score": cer_score,
            "BERTScore": bertscore,
            "METEOR_score": meteor_score,
            "Cleaned_WER_score": cleaned_wer_score,
            "Cleaned_CER_score": cleaned_cer_score,
            "Cleaned_BERTScore": cleaned_bertscore,
            "Cleaned_METEOR_score": cleaned_meteor_score
        }

        return eval_result

    def evaluate_with_llm(self, reference: str, model: str) -> Dict:
        """Evaluate a transcription pair using the LLM."""
        # Assuming LLMEvaluator.evaluate_pair handles preprocessing if needed
        return self.llm_evaluator.evaluate_pair(reference=reference, model=model)


if __name__ == "__main__":
    evaluator = Evaluator()
    all_results = []
    RESULTS_DIR = PROJECT_ROOT / "EVAL" / "transcribe" / "results" 
    transcription_files = glob.glob(str(RESULTS_DIR / '**/*.txt'), recursive=True)
    print(f"Found {len(transcription_files)} transcription files.")
    if not transcription_files:
        print("No transcription files found.")
        exit(1)

    for file_path in transcription_files:

        # Convert file_path to a Path object for easier manipulation
        p_file_path = Path(file_path)

        # Get the path relative to RESULTS_DIR
        relative_path_from_results = p_file_path.relative_to(RESULTS_DIR)

        # The parts will now be: (model_name, audio_file_name, filename.txt)
        if len(relative_path_from_results.parts) >= 2:
            model_name = relative_path_from_results.parts[0]
            audio_file_name = relative_path_from_results.parts[1]
            print(f"Correct Pathing for model: {model_name}, audio file: {audio_file_name}")
        else:
            print(f"Warning: Could not extract model_name and audio_file_name from {file_path}")
            user_input = input("Do you want to continue? (yes/no): ").strip().lower()
            if user_input != 'yes':
                print("Exiting evaluation due to incorrect file path structure.")
                exit(1)
            else:
                print("Continuing evaluation despite incorrect file path structure.")
                print(f"Skipping evaluation for this file: {file_path}.")
                # Skip this file and continue with the next one
                continue

    for file_path in transcription_files:
        try:
            # Convert file_path to a Path object for easier manipulation
            p_file_path = Path(file_path)

            # Get the path relative to RESULTS_DIR
            relative_path_from_results = p_file_path.relative_to(RESULTS_DIR)

            # The parts will now be: (model_name, audio_file_name, filename.txt)
            if len(relative_path_from_results.parts) >= 2:
                model_name = relative_path_from_results.parts[0]
                audio_file_name = relative_path_from_results.parts[1]
                print(f"Processing model: {model_name}, audio file: {audio_file_name}")
            else:
                print(f"Warning: Could not extract model_name and audio_file_name from {file_path}. Skipping.")
                continue

            # Read transcription content
            with open(file_path, 'r', encoding='utf-8') as f:
                transcription = f.read()

            # Construct path to correct transcription file
            CORRECT_TRANSCRIPTIONS_DIR = PROJECT_ROOT / "EVAL" / "evaluation" / "correct_transcriptions"
            correct_transcription_path = CORRECT_TRANSCRIPTIONS_DIR / f'{audio_file_name}.txt'

            # Read correct transcription content
            correct_transcription = ""
            if correct_transcription_path.exists():
                with correct_transcription_path.open('r', encoding='utf-8') as f:
                    correct_transcription = f.read()
            else:
                print(f"Correct transcription path not found: {correct_transcription_path}")
                print(f"Warning: Correct transcription not found for {audio_file_name}. Skipping evaluation for this file.")
                continue # Skip evaluation if correct transcription is missing

            # Evaluate transcription
            result = evaluator.evaluate_transcription(
                model_name=model_name,
                audio_file_name=audio_file_name,
                transcription_type='text', # Assuming all are text for now
                transcription=transcription,
                correct_transcription=correct_transcription
            )

            # Perform LLM evaluation and merge results
            llm_result = evaluator.evaluate_with_llm(correct_transcription, transcription)
            if llm_result:
                # Calculate average LLM score
                llm_eval_score = (llm_result.get("kontextuell_korrekthet", 0) + llm_result.get("overgripande_forstaelse", 0)) / 2
                # save score normalized to 0-1 range
                llm_eval_score = max(0, min(1, llm_eval_score))  # Ensure score is between 0 and 1
                llm_eval_korrekthet = llm_result.get("kontextuell_korrekthet", 0)
                llm_eval_forstaelse = llm_result.get("overgripande_forstaelse", 0)
                # Add LLM evaluation results to the result dictionary
                result["llm_eval_score"] = llm_eval_score
                result["llm_eval_kontextuell_korrekthet"] = llm_eval_korrekthet 
                result["llm_eval_overgripande_forstaelse"] = llm_eval_forstaelse
                # Add any additional LLM evaluation comments
                result["llm_eval_kommentar"] = llm_result.get("kommentar", "")
                result.update(llm_result) # Merge LLM results into the main result

            all_results.append(result)

        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            continue # Continue to the next file if an error occurs

    # Write results to CSV
    if all_results:
        csv_file_path = PROJECT_ROOT / 'EVAL' / 'evaluation' / 'evaluation_results.csv'
        fieldnames = [
            "model", "audio_file", "WER_score", "CER_score", "BERTScore",
            "METEOR_score", "Cleaned_WER_score", "Cleaned_CER_score",
            "Cleaned_BERTScore", "Cleaned_METEOR_score",
            "llm_eval_score", "llm_eval_kontextuell_korrekthet", "llm_eval_overgripande_forstaelse", "llm_eval_kommentar" 
        ]
        with csv_file_path.open('w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for result in all_results:
                # Ensure all required fields are present, add empty string if missing
                row = {field: result.get(field, "") for field in fieldnames}
                writer.writerow(row)

        print(f"Evaluation results written to {csv_file_path}")
    else:
        print("No transcription files found or processed.")