#!/usr/bin/env python3
"""
Diagnostic script to check Ollama connection and model availability.
"""

import requests
import json
import sys
import argparse

def detect_api_type(server_url, timeout=5):
    """Detect if server is llamafile (OpenAI-compatible) or Ollama."""
    try:
        # Try llamafile first (OpenAI-compatible)
        response = requests.get(f"{server_url}/v1/models", timeout=timeout)
        if response.status_code == 200:
            return "llamafile"
    except:
        pass
    
    try:
        # Try Ollama
        response = requests.get(f"{server_url}/api/tags", timeout=timeout)
        if response.status_code == 200:
            return "ollama"
    except:
        pass
    
    return "unknown"

def check_server_status(host="localhost:11434", timeout=10):
    """Check if server is running and get basic info."""
    try:
        # Build server URL
        if not host.startswith('http'):
            server_url = f"http://{host}"
        else:
            server_url = host
            
        print(f"Checking server status at {server_url}...")
        
        # Detect API type
        api_type = detect_api_type(server_url, timeout=timeout)
        
        if api_type == "llamafile":
            response = requests.get(f"{server_url}/v1/models", timeout=timeout)
        elif api_type == "ollama":
            response = requests.get(f"{server_url}/api/tags", timeout=timeout)
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

def test_model(model_name, host="localhost:11434", timeout=60):
    """Test a specific model with a simple request."""
    print(f"\nTesting model '{model_name}'...")
    
    # Build server URL
    if not host.startswith('http'):
        server_url = f"http://{host}"
    else:
        server_url = host
    
    # Detect API type
    api_type = detect_api_type(server_url, timeout=timeout)
    
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
            timeout=timeout
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
    parser.add_argument('--model', required=False,
                       help='Model name to test. If omitted, tests the first available model')
    parser.add_argument('--timeout', type=int, default=60,
                       help='Request timeout in seconds (default: 60)')
    
    args = parser.parse_args()
    
    print("Server Connection Diagnostic Tool")
    print("=" * 40)
    
    # Check server status
    models = check_server_status(args.host, timeout=args.timeout)
    
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
    
    # Determine which model to test
    model_to_test = None
    if args.model:
        # Warn if the provided model is not among available models
        available_names = []
        if isinstance(models, list):
            for m in models:
                if isinstance(m, dict):
                    name = m.get('name') or m.get('id')
                    if name:
                        available_names.append(name)
                else:
                    available_names.append(str(m))
        if available_names and args.model not in available_names:
            print(f"⚠ Model '{args.model}' not found in available models. Attempting anyway...")
        model_to_test = args.model
    else:
        # Fallback to first available model
        if isinstance(models[0], dict):
            model_to_test = models[0].get('name') or models[0].get('id')
        else:
            model_to_test = models[0]
    
    if model_to_test:
        test_model(model_to_test, args.host, timeout=args.timeout)
    
    print("\nDiagnostic complete!")

if __name__ == "__main__":
    main()

