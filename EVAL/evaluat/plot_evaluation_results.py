import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Get the directory of the current script
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

# CSV file path
csv_filepath = SCRIPT_DIR / 'evaluation_results.csv'

# Output directory
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

# Define the score metrics to plot
score_metrics = [
    'WER_score', 'CER_score', 'BERTScore', 'METEOR_score',
    'Cleaned_WER_score', 'Cleaned_CER_score', 'Cleaned_METEOR_score', 'Cleaned_BERTScore',
    'llm_eval_score', 'llm_eval_kontextuell_korrekthet', 'llm_eval_overgripande_forstaelse'
]

# Group by model
grouped_by_model = df.groupby('model')

# --- Existing Plots (kept for completeness, can be removed if not needed) ---
# Iterate through each model (Existing plots)
# for model_name, model_data in grouped_by_model:
#     print(f"Processing model: {model_name}")

#     # Iterate through each score metric
#     for metric in score_metrics:
#         if metric not in model_data.columns:
#             print(f"Warning: Metric '{metric}' not found for model '{model_name}'. Skipping.")
#             continue

#         print(f"  Plotting metric: {metric}")

#         # Create plot
#         plt.figure(figsize=(12, 6))

#         # Plot individual audio_file scores
#         plt.scatter(model_data['audio_file'], model_data[metric], label='Individual Audio File Score')

#         # Calculate and plot average score
#         average_score = model_data[metric].mean()
#         plt.axhline(average_score, color='red', linestyle='--', label=f'Average Score ({average_score:.4f})')

#         # Set plot title and labels
#         plt.title(f'{metric} for {model_name}')
#         plt.xlabel('Audio File')
#         plt.ylabel(metric)
#         plt.xticks(rotation=45, ha='right')
#         plt.legend()
#         plt.grid(True)
#         plt.tight_layout()

#         # Save the plot
#         filename = f"{model_name.replace('-', '_').replace(' ', '_')}_{metric}.png"
#         filepath = os.path.join(output_dir, filename)
#         try:
#             plt.savefig(filepath)
#             print(f"  Saved plot to {filepath}")
#         except Exception as e:
#             print(f"Error saving plot {filepath}: {e}")

#         plt.close()

# # 1. For each score metric: Average score of all audio_files, X models
# print("\nGenerating plots: Average score per metric across all models")
# for metric in score_metrics:
#     if metric not in df.columns:
#         print(f"Warning: Metric '{metric}' not found in DataFrame. Skipping.")
#         continue

#     plt.figure(figsize=(12, 6))
#     # Calculate average score for each model for the current metric
#     avg_scores_per_model = df.groupby('model')[metric].mean().sort_values(ascending=False)
#     avg_scores_per_model.plot(kind='bar')

#     plt.title(f'Average {metric} Across All Models')
#     plt.xlabel('Model')
#     plt.ylabel(f'Average {metric}')
#     plt.xticks(rotation=45, ha='right')
#     plt.grid(axis='y')
#     plt.tight_layout()

#     filename = f"average_{metric}_across_models.png"
#     filepath = os.path.join(output_dir, filename)
#     try:
#         plt.savefig(filepath)
#         print(f"Saved plot to {filepath}")
#     except Exception as e:
#         print(f"Error saving plot {filepath}: {e}")
#     plt.close()

# # 2. For each model: Average score of all audio_files, X score matrix
# print("\nGenerating plots: Average score per model across all metrics")
# for model_name, model_data in grouped_by_model:
#     print(f"Processing model for average metric scores: {model_name}")
#     plt.figure(figsize=(12, 6))

#     # Calculate average score for each metric for the current model
#     avg_scores_per_metric = model_data[score_metrics].mean().sort_values(ascending=False)
#     avg_scores_per_metric.plot(kind='bar')

#     plt.title(f'Average Score Across Metrics for {model_name}')
#     plt.xlabel('Score Metric')
#     plt.ylabel('Average Score')
#     plt.xticks(rotation=45, ha='right')
#     plt.grid(axis='y')
#     plt.tight_layout()

#     filename = f"{model_name.replace('-', '_').replace(' ', '_')}_average_across_metrics.png"
#     filepath = os.path.join(output_dir, filename)
#     try:
#         plt.savefig(filepath)
#         print(f"Saved plot to {filepath}")
#     except Exception as e:
#         print(f"Error saving plot {filepath}: {e}")
#     plt.close()

# --- Interactive Grouped Bar Chart ---

def generate_grouped_bar_chart(dataframe, metrics, output_dir):
    """Generates a grouped bar chart for selected models and metrics."""
    available_models = dataframe['model'].unique().tolist()

    print("\nAvailable models:")
    for i, model in enumerate(available_models):
        print(f"{i + 1}. {model}")

    selected_indices = input(f"Enter the numbers of the models to include (comma-separated, e.g., 1,3,5): ")
    try:
        selected_indices = [int(idx.strip()) - 1 for idx in selected_indices.split(',')]
        selected_models = [available_models[i] for i in selected_indices if 0 <= i < len(available_models)]
    except ValueError:
        print("Invalid input. Please enter numbers separated by commas.")
        return

    if not selected_models:
        print("No valid models selected.")
        return

    filtered_df = dataframe[dataframe['model'].isin(selected_models)]

    if not filtered_df.empty:
        # Calculate average scores for selected models across all metrics
        avg_scores_selected_models = filtered_df.groupby('model')[metrics].mean().T

        plt.figure(figsize=(15, 8))
        avg_scores_selected_models.plot(kind='bar', figsize=(15, 8))

        plt.title('Average Score Comparison for Selected Models Across Metrics')
        plt.xlabel('Score Metric')
        plt.ylabel('Average Score')
        plt.xticks(rotation=45, ha='right')
        plt.legend(title='Model')
        plt.grid(axis='y')
        plt.tight_layout()

        # Get output filename from user
        output_filename = input(f"Enter the filename to save the plot (e.g., my_comparison.png): ")
        if not output_filename:
            print("No filename entered. Skipping save.")
            plt.close()
            return

        filepath = os.path.join(output_dir, output_filename)
        try:
            plt.savefig(filepath)
            print(f"Saved plot to {filepath}")
        except Exception as e:
            print(f"Error saving plot {filepath}: {e}")

        plt.close()
    else:
        print("Warning: No data found for selected models for grouped bar chart.")

# Main loop for interactive plotting
while True:
    generate_grouped_bar_chart(df, score_metrics, output_dir)

    another_plot = input("Generate another grouped bar chart? (yes/no): ").lower()
    if another_plot != 'yes':
        break

print("\nInteractive plotting complete.")