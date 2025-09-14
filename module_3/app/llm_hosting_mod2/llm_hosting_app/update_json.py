import json

# I am not sure why but app.py is not creating:
# jsonl -> json
# Using this to convert jsonl -> json
# Input .jsonl file (line-delimited JSON objects)
input_path = "applicant_data.json.jsonl"
output_path = "llm_extend_applicant_data.json"

data = []
with open(input_path, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():  # skip empty lines
            data.append(json.loads(line))

# Write as one JSON array
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Converted {input_path} -> {output_path} with {len(data)} records.")