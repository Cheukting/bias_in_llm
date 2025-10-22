#!/usr/bin/env python3
"""
Diagnostic script to check Ollama connection and model availability.
"""

import requests
import json
import sys
import argparse

def detect_api_type(server_url):
    """Detect if server is llamafile (OpenAI-compatible) or Ollama."""
    try:
        # Try llamafile first (OpenAI-compatible)
        response = requests.get(f"{server_url}/v1/models", timeout=5)
        if response.status_code == 200:
            return "llamafile"
    except:
        pass
    
    try:
        # Try Ollama
        response = requests.get(f"{server_url}/api/tags", timeout=5)
        if response.status_code == 200:
            return "ollama"
    except:
        pass
    
    return "unknown"

def check_server_status(host="localhost:11434"):
    """Check if server is running and get basic info."""
    try:
        # Build server URL
        if not host.startswith('http'):
            server_url = f"http://{host}"
        else:
            server_url = host
            
        print(f"Checking server status at {server_url}...")
        
        # Detect API type
        api_type = detect_api_type(server_url)
        
        if api_type == "llamafile":
            response = requests.get(f"{server_url}/v1/models", timeout=10)
        elif api_type == "ollama":
            response = requests.get(f"{server_url}/api/tags", timeout=10)
        else:
            print("✗ Cannot detect server type (neither llamafile nor Ollama)")
            return []
        
        if response.status_code == 200:
            print(f"✓ {api_type} server is running")
            data = response.json()
            
            if api_type == "llamafile":
                models = data.get('data', [])
                if models:
                    print(f"Available models ({len(models)}):")
                    for model in models:
                        name = model.get('id', 'Unknown')
                        print(f"  - {name}")
                    return models
                else:
                    print("⚠ No models found in llamafile server")
                    return []
            else:  # ollama
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
        print("✗ Cannot connect to server")
        print("Make sure server is running:")
        print("  - Ollama: ollama serve")
        print("  - llamafile: ./model.llamafile --server --port 8080")
        return []
    except requests.exceptions.Timeout:
        print("✗ Connection timed out")
        return []
    except Exception as e:
        print(f"✗ Error: {e}")
        return []

def test_model(model_name, host="localhost:11434"):
    """Test a specific model with a simple request."""
    print(f"\nTesting model '{model_name}'...")
    
    # Build server URL
    if not host.startswith('http'):
        server_url = f"http://{host}"
    else:
        server_url = host
    
    # Detect API type
    api_type = detect_api_type(server_url)
    
    if api_type == "llamafile":
        # OpenAI-compatible API format
        payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "stream": False
        }
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer sk-local-123'
        }
        api_endpoint = f"{server_url}/v1/chat/completions"
    else:  # ollama
        # Ollama API format
        payload = {
            "model": model_name,
            "prompt": "Hello",
            "stream": False
        }
        headers = {'Content-Type': 'application/json'}
        api_endpoint = f"{server_url}/api/generate"
    
    try:
        response = requests.post(
            api_endpoint,
            json=payload,
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if api_type == "llamafile":
                response_text = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            else:  # ollama
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
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Diagnose Ollama connection and model availability')
    parser.add_argument('--host', default='localhost:11434', 
                       help='Server host and port (default: localhost:11434)')
    
    args = parser.parse_args()
    
    print("Server Connection Diagnostic Tool")
    print("=" * 40)
    
    # Check server status
    models = check_server_status(args.host)
    
    if not models:
        print("\nTroubleshooting steps:")
        print("1. Start server:")
        print("   - Ollama: ollama serve")
        print("   - llamafile: ./model.llamafile --server --port 8080")
        print("2. Download a model:")
        print("   - Ollama: ollama pull llama3.2")
        print("   - llamafile: Download .llamafile from Hugging Face")
        print("3. Check if port is available")
        print(f"4. Verify host is correct: {args.host}")
        sys.exit(1)
    
    # Test the first available model
    if models:
        if isinstance(models[0], dict):
            # Ollama format
            first_model = models[0]['name']
        else:
            # llamafile format (string)
            first_model = models[0]
        test_model(first_model, args.host)
    
    print("\nDiagnostic complete!")

if __name__ == "__main__":
    main()

