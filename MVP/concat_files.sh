#!/bin/bash

# Create or clear the output file
> all_files.txt

# Function to process a single file
process_file() {
    local file="$1"
    
    # Write the command to the output file
    echo "cat $file" >> all_files.txt
    echo "----- Begin output of $file -----" >> all_files.txt
    
    # Check if it's a .env file
    if [[ "$file" == *.env ]]; then
        # Process .env file line by line and replace values after =
        while IFS='=' read -r key value; do
            # Skip empty lines or comments
            [[ -z "$key" || "$key" =~ ^# ]] && continue
            # Output the key with placeholder
            echo "${key}=place holder for value" >> all_files.txt
        done < "$file"
    else
        # For non-.env files, just cat the contents
        cat "$file" >> all_files.txt
    fi
    
    # Add separator after file content
    echo "----- End output of $file -----" >> all_files.txt
    echo "" >> all_files.txt
}

# Process all files including hidden ones and subdirectories
find . -type f -print0 | while IFS= read -r -d '' file; do
    # Remove leading ./ from the filename
    file="${file#./}"
    process_file "$file"
done

echo "Contents of all files (including hidden files and subdirectories) have been saved to all_files.txt"