import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Get the directory of the current script
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
csv_filepath = SCRIPT_DIR / 'evaluation_results.csv'
output_dir = SCRIPT_DIR / "plots"

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# Read the CSV data into a pandas DataFrame
try:
    df = pd.read_csv(csv_filepath)
except FileNotFoundError:
    print(f"Error: CSV file not found at {csv_filepath}")
    exit()
except Exception as e:
    print(f"Error reading CSV data from {csv_filepath}: {e}")
    exit()

# Define score metrics, separating base and cleaned scores
base_metrics = ['WER_score', 'CER_score', 'BERTScore', 'METEOR_score']
cleaned_metrics = ['Cleaned_WER_score', 'Cleaned_CER_score', 'Cleaned_BERTScore', 'Cleaned_METEOR_score']

def compare_scores_for_model(dataframe):
    """Compare score and cleaned score metrics for a single selected model with grouped bars."""
    available_models = dataframe['model'].unique().tolist()
    
    print("\nAvailable models:")
    for i, model in enumerate(available_models):
        print(f"{i + 1}. {model}")
    
    selected_index = input("Enter the number of the model to compare (e.g., 1): ")
    try:
        selected_index = int(selected_index.strip()) - 1
        if 0 <= selected_index < len(available_models):
            selected_model = available_models[selected_index]
        else:
            print("Invalid selection. Exiting.")
            return
    except ValueError:
        print("Invalid input. Please enter a number. Exiting.")
        return
    
    # Filter data for the selected model
    model_data = dataframe[dataframe['model'] == selected_model]
    
    # Calculate average scores for base and cleaned metrics
    avg_base_scores = model_data[base_metrics].mean()
    avg_cleaned_scores = model_data[cleaned_metrics].mean()
    
    # Metric names for x-axis (without 'score' suffix for cleaner labels)
    metric_names = [metric.replace('_score', '') for metric in base_metrics]
    
    # Set up positions for grouped bars
    x = np.arange(len(metric_names))  # Positions for the groups
    width = 0.35  # Width of the bars
    
    # Create figure
    plt.figure(figsize=(12, 6))
    
    # Plot base scores
    plt.bar(x - width/2, avg_base_scores, width, label='Base Score', color='b')
    
    # Plot cleaned scores
    plt.bar(x + width/2, avg_cleaned_scores, width, label='Cleaned Score', color='g')
    
    # Set plot title and labels
    plt.title(f'Grouped Comparison of Scores and Cleaned Scores for {selected_model}')
    plt.xlabel('Metric')
    plt.ylabel('Average Score')
    plt.xticks(x, metric_names, rotation=45, ha='right')
    plt.legend()
    plt.grid(axis='y')
    plt.tight_layout()
    
    # Ask for save filename
    output_filename = input(f"Enter the filename to save the plot (e.g., model_comparison_grouped.png): ")
    if not output_filename:
        print("No filename entered. Skipping save.")
        plt.close()
        return
    
    filepath = output_dir / output_filename
    try:
        plt.savefig(filepath)
        print(f"Saved plot to {filepath}")
    except Exception as e:
        print(f"Error saving plot {filepath}: {e}")
    
    plt.close()

# Main loop for interactive comparison
while True:
    compare_scores_for_model(df)
    another_comparison = input("Perform another comparison? (yes/no): ").lower()
    if another_comparison != 'yes':
        break

print("\nComparison script complete.")