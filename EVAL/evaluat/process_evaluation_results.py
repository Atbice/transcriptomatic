import pandas as pd

def process_evaluation_results(input_csv_path, output_csv_path):
    """
    Reads an evaluation results CSV, removes a specific column,
    groups by 'model', calculates the average of numerical columns,
    and saves the averaged results to a new CSV.
    """
    try:
        # 1. Read the CSV file
        df = pd.read_csv(input_csv_path)

        # 2. Remove the column named 'llm_eval_kommentar'
        if 'llm_eval_kommentar' in df.columns:
            df = df.drop(columns=['llm_eval_kommentar'])
        else:
            print(f"Warning: 'llm_eval_kommentar' column not found in {input_csv_path}")

        # 3. Group the data by the 'model' column and 4. Calculate the average of all numerical columns
        # pandas .mean() automatically handles non-numeric columns by excluding them
        averaged_df = df.groupby('model').mean(numeric_only=True).reset_index()

        # 5. Save the resulting DataFrame to a new CSV file
        averaged_df.to_csv(output_csv_path, index=False)
        print(f"Processed data saved to {output_csv_path}")

    except FileNotFoundError:
        print(f"Error: Input file not found at {input_csv_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    input_file = 'evaluation/evaluation_results.csv'
    output_file = 'evaluation/evaluation_results_averaged.csv'
    process_evaluation_results(input_file, output_file)