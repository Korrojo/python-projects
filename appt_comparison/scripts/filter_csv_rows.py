import pandas as pd

# Define file paths
source_file = "/Users/demesew_abebe@optum.com/Downloads/Daily_Appointment_Comparison_input_20251028.csv"
destination_file = "/Users/demesew_abebe@optum.com/Downloads/Daily_Appointment_Comparison_input1_20251028.csv"

# Define the filter value
filter_value = "compare with staff availability history collection"

try:
    # Read the CSV file into a pandas DataFrame
    df = pd.read_csv(source_file)

    # Clean up column names to remove leading/trailing whitespace
    df.columns = df.columns.str.strip()

    # --- Debugging: Print column names ---
    print("Columns found in the CSV file:")
    print(list(df.columns))
    # --- End Debugging ---

    # Filter the DataFrame
    # Using .astype(str) to handle potential non-string data and avoid errors
    filtered_df = df[df["Comment2"].astype(str) == filter_value]

    # Save the filtered DataFrame to a new CSV file
    filtered_df.to_csv(destination_file, index=False)

    print(f"Successfully filtered the data and saved it to {destination_file}")
    print(f"Original rows: {len(df)}")
    print(f"Filtered rows: {len(filtered_df)}")

except FileNotFoundError:
    print(f"Error: The source file was not found at {source_file}")
except KeyError:
    print("Error: The required column 'Comment2' was not found in the CSV file.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
