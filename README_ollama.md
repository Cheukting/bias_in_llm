# Server OpenSource Model

Simple script to process text from CSV files using local AI models.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start a server:**
   ```bash
   # Option A: Ollama
   ollama serve
   
   # Option B: llamafile
   ./model.llamafile --server --port 8080
   ```

3. **Download a model:**
   ```bash
   # Option A: Ollama
   ollama pull llama3.2
   
   # Option B: llamafile
   # Download .llamafile from Hugging Face
   ```

4. **Run the script:**
   ```bash
   python serve_os_model.py
   ```

## Usage

**Basic usage:**
```bash
python serve_os_model.py
```

**With custom settings:**
```bash
python serve_os_model.py --host localhost:11434 --model llama3.2 --csv my_data.csv --output my_results.json
```

**Remote server:**
```bash
# Ollama server
python serve_os_model.py --host 192.168.1.100:11434 --model llama3.2

# llamafile server
python serve_os_model.py --host 192.168.1.100:8080 --model llama3.2
```

## Troubleshooting

If you get connection errors, run the diagnostic tool first:
```bash
python diagnose_connection.py
```

**With custom host:**
```bash
# Ollama server
python diagnose_connection.py --host 192.168.1.100:11434

# llamafile server  
python diagnose_connection.py --host 192.168.1.100:8080
```

This will check:
- ✅ Server is running
- ✅ Models are available  
- ✅ Model responds correctly

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--host` | Server host and port | `localhost:11434` |
| `--model` | Model name to use | `llama3.2` |
| `--csv` | Input CSV file | `sample_data.csv` |
| `--output` | Output JSON file | `results.json` |

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
