if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <search_string> <file_name>"
    exit 1
fi

search_str="$1"

file_name="$2"

output_file="search_result_$(date +%Y%m%d_%H%M%S).txt"

if [ ! -f "$file_name" ]; then
    echo "Error: File '$file_name' does not exist."
    exit 1
fi

grep -ni "$search_str" "$file_name" | tee "$output_file"

echo "Search completed. Results saved to '$output_file'"
