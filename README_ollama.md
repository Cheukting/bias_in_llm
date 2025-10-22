# Server OpenSource Model

Simple script to process text from CSV files using local AI models.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Ollama server:**
   ```bash
   ollama serve
   ```

3. **Download a model:**
   ```bash
   ollama pull llama3.2
   ```

## Usage

1. Update the model name in `serve_os_model.py` if needed (default: "llama3.2")
2. Replace `sample_data.csv` with your actual CSV file
3. Run the script:
   ```bash
   python serve_os_model.py
   ```

## Troubleshooting

If you get connection errors, run the diagnostic tool first:
```bash
python diagnose_connection.py
```

This will check:
- ✅ Server is running
- ✅ Models are available  
- ✅ Model responds correctly

## Configuration

Edit these variables in the script:
- `SERVER_URL`: Server URL (default: "http://localhost:11434")
- `MODEL_NAME`: Your downloaded model name (default: "llama3.2")
- `CSV_FILE`: Path to your CSV file (default: "sample_data.csv")
- `OUTPUT_FILE`: Path to save results (default: "results.json")

## CSV Format

Single column with text prompts:
```csv
text
"Hello, how are you?"
"What is AI?"
```

## Output

Results are saved as JSON with the following structure:
```json
[
  {
    "row_number": 1,
    "input_text": "Your prompt",
    "response": "Model's response"
  }
]
```
