import pandas as pd
import sys
import os

def normalize_column(series):
    """Divides a pandas Series by 10."""
    # Attempt to convert column to numeric, coercing errors
    numeric_series = pd.to_numeric(series, errors='coerce')
    # Handle potential division by zero or non-numeric values after coercion
    return numeric_series / 10.0

def main():
    csv_file = input("Enter the path to the CSV file: ")

    if not os.path.exists(csv_file):
        print(f"Error: File not found at {csv_file}", file=sys.stderr)
        sys.exit(1)

    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        print(f"Error reading CSV file: {e}", file=sys.stderr)
        sys.exit(1)

    print("\nAvailable columns:")
    for i, col in enumerate(df.columns):
        print(f"{i + 1}. {col}")

    column_input = input("\nEnter the numbers of the columns to normalize (separated by spaces): ")
    try:
        selected_indices = [int(num) - 1 for num in column_input.split()]
        columns_to_normalize = [df.columns[i] for i in selected_indices if 0 <= i < len(df.columns)]
    except ValueError:
        print("Error: Invalid input. Please enter numbers separated by spaces.", file=sys.stderr)
        sys.exit(1)
    except IndexError:
        print("Error: Invalid column number entered.", file=sys.stderr)
        sys.exit(1)

    if not columns_to_normalize:
        print("No valid columns selected for normalization.", file=sys.stderr)
        sys.exit(0)

    # Normalize selected columns
    for col in columns_to_normalize:
        try:
            df[col] = normalize_column(df[col])
            # Optional: Handle rows that became NaN after normalization if needed,
            # currently they will remain NaN.
        except Exception as e:
            print(f"Error normalizing column '{col}': {e}", file=sys.stderr)
            sys.exit(1)

    # Overwrite the original file
    try:
        df.to_csv(csv_file, index=False)
        print(f"\nSuccessfully normalized columns {', '.join(columns_to_normalize)} in {csv_file}")
    except Exception as e:
        print(f"Error writing normalized data back to {csv_file}: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()