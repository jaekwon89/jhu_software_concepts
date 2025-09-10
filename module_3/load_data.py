import json



def load_json(path="../module_2/llm_extend_applicant_data.json"):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def main():
    data = load_json()
    

