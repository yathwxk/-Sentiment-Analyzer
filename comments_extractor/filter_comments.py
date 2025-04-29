import json
import sys

if len(sys.argv) != 3:
    print("Usage: python filter_comments.py <input_file> <output_file>")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]

with open(input_file, 'r', encoding='utf-8') as file:
    data = json.load(file)

def extract_comments(data):
    comments = []

    if isinstance(data, list):
        for item in data:
            comments.extend(extract_comments(item))

    elif isinstance(data, dict):
        if 'text' in data:
            comment = {
                'author': data.get('author', 'Unknown'),
                'author_id': data.get('author_id', 'Unknown'),
                'text': data['text'],
                'author_url': data.get('author_url', 'Unknown'),
                'like_count': data.get('like_count', 0),
                'time': data.get('_time_text', 'Unknown time')
            }
            comments.append(comment)
        for key, value in data.items():
            comments.extend(extract_comments(value))

    return comments

filtered_comments = extract_comments(data)

with open(output_file, 'w', encoding='utf-8') as out_file:
    json.dump(filtered_comments, out_file, indent=4, ensure_ascii=False)

print(f"Filtered comments saved to '{output_file}'.")
