#!/usr/bin/env python3
"""
Simple script to connect to Ollama server and process text from CSV file.
"""

import csv
import os
import requests
import json
import sys
import argparse
from typing import List, Dict

class ServeOSModel:
    def __init__(self, server_url: str = "http://localhost:11434", model_name: str = "llama3.2"):
        """
        Initialize the processor with server details.
        
        Args:
            server_url: URL of the server (default: http://localhost:11434)
            model_name: Name of the model to use (default: llama3.2)
        """
        self.server_url = server_url
        self.model_name = model_name
        self.api_type = self._detect_api_type()
        
        if self.api_type == "llamafile":
            self.api_url = f"{server_url}/v1/chat/completions"
        else:  # ollama
            self.api_url = f"{server_url}/api/generate"
    
    def _detect_api_type(self) -> str:
        """Detect if server is llamafile (OpenAI-compatible) or Ollama."""
        try:
            # Try llamafile first (OpenAI-compatible)
            response = requests.get(f"{self.server_url}/v1/models", timeout=5)
            if response.status_code == 200:
                return "llamafile"
        except:
            pass
        
        try:
            # Try Ollama
            response = requests.get(f"{self.server_url}/api/tags", timeout=5)
            if response.status_code == 200:
                return "ollama"
        except:
            pass
        
        # Default to ollama if detection fails
        return "ollama"
    
    def check_server_connection(self) -> bool:
        """Check if server is running and accessible."""
        try:
            if self.api_type == "llamafile":
                response = requests.get(f"{self.server_url}/v1/models", timeout=5)
            else:  # ollama
                response = requests.get(f"{self.server_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available models from server."""
        try:
            if self.api_type == "llamafile":
                response = requests.get(f"{self.server_url}/v1/models")
                if response.status_code == 200:
                    models = response.json().get('data', [])
                    return [model['id'] for model in models]
            else:  # ollama
                response = requests.get(f"{self.server_url}/api/tags")
                if response.status_code == 200:
                    models = response.json().get('models', [])
                    return [model['name'] for model in models]
            return []
        except requests.exceptions.RequestException:
            return []
    
    def send_message(self, text: str, timeout: int = 120) -> str:
        """
        Send a text message to server and get response.
        
        Args:
            text: The input text to send to the model
            timeout: Request timeout in seconds (default: 120)
            
        Returns:
            The model's response as a string
        """
        if self.api_type == "llamafile":
            # OpenAI-compatible API format
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "user", "content": text}
                ],
                "stream": False
            }
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer sk-local-123'  # llamafile doesn't validate this
            }
        else:  # ollama
            # Ollama API format
            payload = {
                "model": self.model_name,
                "prompt": text,
                "stream": False
            }
            headers = {'Content-Type': 'application/json'}
        
        try:
            print(f"  Sending request to {self.api_type} model '{self.model_name}'...")
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=timeout
            )
            response.raise_for_status()
            
            result = response.json()
            
            if self.api_type == "llamafile":
                return result.get('choices', [{}])[0].get('message', {}).get('content', 'No response received')
            else:  # ollama
                return result.get('response', 'No response received')
            
        except requests.exceptions.Timeout:
            return f"Error: Request timed out after {timeout} seconds. Model may be too slow or overloaded."
        except requests.exceptions.ConnectionError:
            return f"Error: Cannot connect to server. Make sure the server is running."
        except requests.exceptions.RequestException as e:
            return f"Error: {str(e)}"
    
    def test_model_connection(self) -> bool:
        """Test if the model is working with a simple request."""
        print("Testing model connection with a simple request...")
        test_response = self.send_message("Hello", timeout=30)
        if test_response.startswith("Error:"):
            print(f"Model test failed: {test_response}")
            return False
        else:
            print(f"Model test successful: {test_response[:50]}...")
            return True
    
    def process_csv(self, csv_file_path: str, output_file_path: str = None, checkpoint_file: str = None, save_every: int = 50, resume: bool = True, output_mode: str = None) -> List[Dict]:
        """
        Process text from CSV file and get responses from Ollama.
        
        Args:
            csv_file_path: Path to the input CSV file
            output_file_path: Optional path to save results (default: None)
            checkpoint_file: Optional path to save progress for resuming
            save_every: Save results and checkpoint every N processed rows
            resume: If True and checkpoint exists, resume from last position
            output_mode: 'json' or 'jsonl'. If None, inferred from output path extension
            
        Returns:
            List of dictionaries containing input text and responses
        """
        session_results = []  # results processed in this invocation
        all_results = []      # complete results if using JSON array mode
        processed_since_save = 0
        last_absolute_index = 0  # absolute CSV row index (1-based)
        processed_count = 0      # count of processed (non-empty, non-header) rows in total for this run
        mode = output_mode
        
        if mode is None and output_file_path:
            lower = output_file_path.lower()
            mode = 'jsonl' if lower.endswith('.jsonl') else 'json'
        if mode is None:
            mode = 'json'
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                # Assume CSV has a single column of text
                reader = csv.reader(file)
                rows = list(reader)
                # Explicitly skip header row
                header = rows[0] if rows else None
                data_rows = rows[1:] if len(rows) > 1 else []
                # Count only non-empty data rows
                total_rows = len([row for row in data_rows if row and row[0].strip()])
                
                # Load checkpoint if requested
                if resume and checkpoint_file and os.path.exists(checkpoint_file):
                    try:
                        with open(checkpoint_file, 'r', encoding='utf-8') as cf:
                            ckpt = json.load(cf)
                            last_absolute_index = int(ckpt.get('last_absolute_index', 0))
                            processed_count = int(ckpt.get('processed_count', 0))
                            print(f"Resuming from checkpoint at absolute row {last_absolute_index} ({processed_count}/{total_rows} processed).")
                    except Exception as e:
                        print(f"Warning: Could not load checkpoint '{checkpoint_file}': {e}. Starting fresh.")
                        last_absolute_index = 0
                        processed_count = 0
                
                # If JSON array mode and resuming, try to load existing results
                if output_file_path and mode == 'json' and os.path.exists(output_file_path):
                    try:
                        with open(output_file_path, 'r', encoding='utf-8') as rf:
                            loaded = json.load(rf)
                            if isinstance(loaded, list):
                                all_results = loaded
                            else:
                                all_results = []
                    except Exception:
                        all_results = []
                
                print(f"Found {total_rows} rows to process")
                
                def save_checkpoint_if_needed(force: bool = False):
                    nonlocal processed_since_save
                    if not checkpoint_file:
                        return
                    if (processed_since_save >= save_every) or force:
                        try:
                            ckpt_data = {
                                'last_absolute_index': last_absolute_index,
                                'processed_count': processed_count,
                                'total_rows': total_rows,
                                'output_file': output_file_path,
                                'output_mode': mode,
                                'model_name': self.model_name,
                                'api_type': self.api_type,
                            }
                            with open(checkpoint_file, 'w', encoding='utf-8') as cf:
                                json.dump(ckpt_data, cf, indent=2, ensure_ascii=False)
                            print(f"Checkpoint saved at absolute row {last_absolute_index} ({processed_count}/{total_rows}).")
                            processed_since_save = 0
                        except Exception as e:
                            print(f"Warning: Failed to save checkpoint: {e}")
                
                def save_results_if_needed(force: bool = False):
                    nonlocal processed_since_save
                    if not output_file_path:
                        return
                    if mode == 'json':
                        if (processed_since_save >= save_every) or force:
                            try:
                                with open(output_file_path, 'w', encoding='utf-8') as of:
                                    json.dump(all_results, of, indent=2, ensure_ascii=False)
                                print(f"Results saved to: {output_file_path}")
                                processed_since_save = 0
                            except Exception as e:
                                print(f"Warning: Failed to save results: {e}")
                    # jsonl is written per-row; nothing to batch-save other than checkpoint
                
                for data_index, row in enumerate(data_rows, 1):
                    # Skip already processed data indices
                    if data_index <= last_absolute_index:
                        continue
                    if (not row) or (not row[0].strip()):  # Skip empty rows
                        continue
                    
                    text = row[0].strip()
                    print(f"\nProcessing row {data_index}/{total_rows}: {text[:50]}...")
                    
                    response = self.send_message(text)
                    
                    result = {
                        'row_number': data_index,
                        'input_text': text,
                        'response': response
                    }
                    session_results.append(result)
                    processed_count += 1
                    processed_since_save += 1
                    last_absolute_index = data_index
                    
                    # Persist output
                    if output_file_path:
                        if mode == 'jsonl':
                            try:
                                with open(output_file_path, 'a', encoding='utf-8') as of:
                                    of.write(json.dumps(result, ensure_ascii=False))
                                    of.write('\n')
                            except Exception as e:
                                print(f"Warning: Failed to append to JSONL results: {e}")
                        else:
                            all_results.append(result)
                    
                    # Periodic saves
                    save_results_if_needed(force=False)
                    save_checkpoint_if_needed(force=False)
                    
                    print(f"Response: {response[:100]}...")
                    print("-" * 50)
        
        except FileNotFoundError:
            print(f"Error: CSV file '{csv_file_path}' not found.")
            return []
        except Exception as e:
            print(f"Error processing CSV: {str(e)}")
            return []
        
        # Save results if output file is specified
        if output_file_path:
            if mode == 'json':
                # Final save for JSON array mode
                try:
                    with open(output_file_path, 'w', encoding='utf-8') as of:
                        json.dump(all_results, of, indent=2, ensure_ascii=False)
                    print(f"Results saved to: {output_file_path}")
                except Exception as e:
                    print(f"Error saving results: {str(e)}")
            # jsonl already saved incrementally
        
        # Always save a final checkpoint
        if checkpoint_file:
            try:
                with open(checkpoint_file, 'w', encoding='utf-8') as cf:
                    json.dump({
                        'last_absolute_index': last_absolute_index,
                        'processed_count': processed_count,
                        'total_rows': total_rows,
                        'output_file': output_file_path,
                        'output_mode': mode,
                        'model_name': self.model_name,
                        'api_type': self.api_type,
                    }, cf, indent=2, ensure_ascii=False)
                print(f"Final checkpoint saved at absolute row {last_absolute_index} ({processed_count}/{total_rows}).")
            except Exception as e:
                print(f"Warning: Failed to save final checkpoint: {e}")
        
        return session_results
    
    def save_results(self, results: List[Dict], output_file_path: str):
        """Save results to a JSON file."""
        try:
            with open(output_file_path, 'w', encoding='utf-8') as file:
                json.dump(results, file, indent=2, ensure_ascii=False)
            print(f"Results saved to: {output_file_path}")
        except Exception as e:
            print(f"Error saving results: {str(e)}")


def main():
    """Main function to run the processor."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process CSV text with local AI model')
    parser.add_argument('--host', default='localhost:11434', 
                       help='Server host and port (default: localhost:11434)')
    parser.add_argument('--model', default='llama3.2', 
                       help='Model name (default: llama3.2)')
    parser.add_argument('--csv', default='sample_data.csv', 
                       help='CSV file path (default: sample_data.csv)')
    parser.add_argument('--output', default='results.json', 
                       help='Output JSON file (default: results.json)')
    parser.add_argument('--checkpoint', default='results.checkpoint.json', 
                       help='Checkpoint file to save and resume progress (default: results.checkpoint.json)')
    parser.add_argument('--save-every', type=int, default=50, 
                       help='Save results and checkpoint every N rows (default: 50)')
    parser.add_argument('--fresh', action='store_true', 
                       help='Ignore checkpoint and start from the beginning')
    parser.add_argument('--output-mode', choices=['json', 'jsonl'], default=None,
                       help='Output mode; defaults to file extension (.jsonl -> jsonl, else json)')
    
    args = parser.parse_args()
    
    # Build server URL
    if not args.host.startswith('http'):
        server_url = f"http://{args.host}"
    else:
        server_url = args.host
    
    # Initialize processor
    processor = ServeOSModel(server_url, args.model)
    
    # Check connection
    print(f"Checking connection to {server_url}...")
    if not processor.check_server_connection():
        print(f"Error: Cannot connect to server at {server_url}")
        print("Make sure the server is running.")
        sys.exit(1)
    
    print(f"✓ Connected to {processor.api_type} server")
    
    # Show available models
    models = processor.get_available_models()
    if models:
        print(f"Available models: {', '.join(models)}")
        if args.model not in models:
            print(f"Warning: Model '{args.model}' not found in available models.")
            print("Use --model <model_name> to specify a different model.")
    else:
        print("Warning: Could not retrieve available models.")
    
    # Test model connection
    print("\nTesting model connection...")
    if not processor.test_model_connection():
        print("Model test failed. Please check:")
        print("1. Model is downloaded: ollama pull <model_name>")
        print("2. Model name is correct (use --model <name>)")
        print("3. Server has enough resources")
        sys.exit(1)
    
    # Process CSV
    print(f"\nProcessing CSV file: {args.csv}")
    results = processor.process_csv(
        args.csv,
        args.output,
        checkpoint_file=args.checkpoint,
        save_every=args.save_every,
        resume=(not args.fresh),
        output_mode=args.output_mode,
    )
    
    if results:
        print(f"\nProcessed {len(results)} rows successfully.")
        if args.output:
            print(f"Results saved to: {args.output}")
    else:
        print("No results to process.")


if __name__ == "__main__":
    main()
