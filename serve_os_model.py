#!/usr/bin/env python3
"""
Simple script to connect to Ollama server and process text from CSV file.
"""

import csv
import requests
import json
import sys
from typing import List, Dict

class ServeOSModel:
    def __init__(self, ollama_url: str = "http://localhost:11434", model_name: str = "llama3.2"):
        """
        Initialize the processor with Ollama server details.
        
        Args:
            ollama_url: URL of the Ollama server (default: http://localhost:11434)
            model_name: Name of the model to use (default: llama3.2)
        """
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.api_url = f"{ollama_url}/api/generate"
    
    def check_ollama_connection(self) -> bool:
        """Check if Ollama server is running and accessible."""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available models from Ollama."""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [model['name'] for model in models]
            return []
        except requests.exceptions.RequestException:
            return []
    
    def send_message(self, text: str, timeout: int = 120) -> str:
        """
        Send a text message to Ollama and get response.
        
        Args:
            text: The input text to send to the model
            timeout: Request timeout in seconds (default: 120)
            
        Returns:
            The model's response as a string
        """
        payload = {
            "model": self.model_name,
            "prompt": text,
            "stream": False
        }
        
        try:
            print(f"  Sending request to model '{self.model_name}'...")
            response = requests.post(
                self.api_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', 'No response received')
            
        except requests.exceptions.Timeout:
            return f"Error: Request timed out after {timeout} seconds. Model may be too slow or overloaded."
        except requests.exceptions.ConnectionError:
            return f"Error: Cannot connect to server. Make sure Ollama is running."
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
    
    def process_csv(self, csv_file_path: str, output_file_path: str = None) -> List[Dict]:
        """
        Process text from CSV file and get responses from Ollama.
        
        Args:
            csv_file_path: Path to the input CSV file
            output_file_path: Optional path to save results (default: None)
            
        Returns:
            List of dictionaries containing input text and responses
        """
        results = []
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                # Assume CSV has a single column of text
                reader = csv.reader(file)
                rows = list(reader)
                total_rows = len([row for row in rows if row and row[0].strip() and not row[0].strip().lower() == 'text'])
                
                print(f"Found {total_rows} rows to process")
                
                for row_num, row in enumerate(reader, 1):
                    if (row_num == 1) or (not row) or (not row[0].strip()):  # Skip header and empty rows
                        continue
                    
                    text = row[0].strip()
                    print(f"\nProcessing row {row_num}/{total_rows}: {text[:50]}...")
                    
                    response = self.send_message(text)
                    
                    result = {
                        'row_number': row_num,
                        'input_text': text,
                        'response': response
                    }
                    results.append(result)
                    
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
            self.save_results(results, output_file_path)
        
        return results
    
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
    # Configuration
    OLLAMA_URL = "http://localhost:11434"
    MODEL_NAME = "openthinker:7b"  # Change this to your downloaded model name
    CSV_FILE = "sample_data.csv"
    OUTPUT_FILE = "results.json"
    
    # Initialize processor
    processor = ServeOSModel(OLLAMA_URL, MODEL_NAME)
    
    # Check connection
    print("Checking Ollama connection...")
    if not processor.check_ollama_connection():
        print("Error: Cannot connect to Ollama server.")
        print("Make sure Ollama is running on", OLLAMA_URL)
        sys.exit(1)
    
    print("✓ Connected to Ollama server")
    
    # Show available models
    models = processor.get_available_models()
    if models:
        print(f"Available models: {', '.join(models)}")
        if MODEL_NAME not in models:
            print(f"Warning: Model '{MODEL_NAME}' not found in available models.")
            print("Please update MODEL_NAME in the script to match your model.")
    else:
        print("Warning: Could not retrieve available models.")
    
    # Test model connection
    print("\nTesting model connection...")
    if not processor.test_model_connection():
        print("Model test failed. Please check:")
        print("1. Model is downloaded: ollama pull <model_name>")
        print("2. Model name is correct in the script")
        print("3. Server has enough resources")
        sys.exit(1)
    
    # Process CSV
    print(f"\nProcessing CSV file: {CSV_FILE}")
    results = processor.process_csv(CSV_FILE, OUTPUT_FILE)
    
    if results:
        print(f"\nProcessed {len(results)} rows successfully.")
        if OUTPUT_FILE:
            print(f"Results saved to: {OUTPUT_FILE}")
    else:
        print("No results to process.")


if __name__ == "__main__":
    main()
