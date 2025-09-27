# Mini LLM Standardizer — Flask (Replit-friendly)

Tiny Flask API that runs a small local LLM (TinyLlama 1.1B, GGUF) via `llama-cpp-python` to standardize
degree program + university names. It appends two new fields to each row:
- `llm-generated-program`
- `llm-generated-university`

## Quickstart (Replit)

1. Create a new **Python** Repl.
2. Upload these files (or import the zip).
3. Install deps:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the API server:
   ```bash
   python app.py --serve
   ```
   The first run downloads a small GGUF model from Hugging Face (defaults to TinyLlama 1.1B Chat Q4_K_M).

5. Test locally (replace the URL with your Replit web URL when deployed):
   ```bash
   curl -s -X POST http://localhost:8000/standardize      -H "Content-Type: application/json"      -d @sample_data.json | jq .
   ```

## CLI mode (no server)

```bash
python app.py --file cleaned_applicant_data.json --stdout > full_out.jsonl
```

## Config (env vars)

- `MODEL_REPO` (default: `TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF`)
- `MODEL_FILE` (default: `tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf`)
- `N_THREADS` (default: CPU count)
- `N_CTX` (default: 2048)
- `N_GPU_LAYERS` (default: 0 — CPU only)

If memory is tight on Replit, try:
```bash
export MODEL_FILE=tinyllama-1.1b-chat-v1.0.Q3_K_M.gguf
```

## Notes
- Strict JSON prompting + a rules-first fallback keep tiny models on task.
- Extend the few-shots and the fallback patterns in `app.py` for higher accuracy on your dataset.
