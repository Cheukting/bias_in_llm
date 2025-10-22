#!/usr/bin/env python3
"""
Diagnostic script to check Ollama connection and model availability.
"""

import requests
import json
import sys

def check_ollama_status():
    """Check if Ollama server is running and get basic info."""
    try:
        print("Checking Ollama server status...")
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        
        if response.status_code == 200:
            print("✓ Ollama server is running")
            data = response.json()
            models = data.get('models', [])
            
            if models:
                print(f"Available models ({len(models)}):")
                for model in models:
                    name = model.get('name', 'Unknown')
                    size = model.get('size', 0)
                    size_gb = size / (1024**3) if size > 0 else 0
                    print(f"  - {name} ({size_gb:.1f} GB)")
                return models
            else:
                print("⚠ No models found. Download a model with: ollama pull <model_name>")
                return []
        else:
            print(f"✗ Server returned status {response.status_code}")
            return []
            
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to Ollama server")
        print("Make sure Ollama is running: ollama serve")
        return []
    except requests.exceptions.Timeout:
        print("✗ Connection timed out")
        return []
    except Exception as e:
        print(f"✗ Error: {e}")
        return []

def test_model(model_name):
    """Test a specific model with a simple request."""
    print(f"\nTesting model '{model_name}'...")
    
    payload = {
        "model": model_name,
        "prompt": "Hello",
        "stream": False
    }
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '')
            print(f"✓ Model responded: {response_text[:100]}...")
            return True
        else:
            print(f"✗ Model test failed with status {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("✗ Model test timed out (model may be too slow)")
        return False
    except Exception as e:
        print(f"✗ Model test error: {e}")
        return False

def main():
    print("Ollama Connection Diagnostic Tool")
    print("=" * 40)
    
    # Check server status
    models = check_ollama_status()
    
    if not models:
        print("\nTroubleshooting steps:")
        print("1. Start Ollama: ollama serve")
        print("2. Download a model: ollama pull llama3.2")
        print("3. Check if port 11434 is available")
        sys.exit(1)
    
    # Test the first available model
    if models:
        first_model = models[0]['name']
        test_model(first_model)
    
    print("\nDiagnostic complete!")

if __name__ == "__main__":
    main()

