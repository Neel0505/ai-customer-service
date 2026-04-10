#!/usr/bin/env python3
"""Run the application and an ngrok tunnel simultaneously in development."""

import subprocess
import time
import requests
import sys

def main():
    print("\n🚀 Starting Omni-Channel Agent in Development Mode...")
    
    # Start uvicorn
    server_process = subprocess.Popen(["uvicorn", "app.main:app", "--reload", "--port", "8000"])
    
    # Start ngrok in background
    print("🔌 Starting ngrok tunnel on port 8000...")
    ngrok_process = subprocess.Popen(["ngrok", "http", "8000"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Wait for ngrok to initialize
    print("⏳ Waiting for ngrok tunnel to be established...")
    time.sleep(4)
    
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=2)
        data = response.json()
        
        if 'tunnels' in data and len(data['tunnels']) > 0:
            public_url = data['tunnels'][0]['public_url']
            print("\n" + "="*60)
            print("✅ Tunnel established successfully!")
            print(f"🌍 Public URL: {public_url}")
            print("="*60)
            print("\n📝 Update your Webhooks to point here:")
            print(f"  👉 WhatsApp:  {public_url}/webhooks/twilio/whatsapp")
            print(f"  👉 Email:     {public_url}/webhooks/email")
            print(f"  👉 Instagram: {public_url}/webhooks/instagram")
            print(f"  👉 Shopify:   {public_url}/webhooks/shopify")
            print("="*60 + "\n")
        else:
            print("⚠️ ngrok is running but no tunnels were found.")
            
    except requests.exceptions.RequestException as e:
        print(f"\n⚠️ Could not fetch ngrok URL automatically (is ngrok authenticated?).")
        print(f"   Error: {e}")
        print("   Make sure you have run: ngrok config add-authtoken <your-token>\n")
    
    try:
        # Keep the script alive while the server runs
        server_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down gracefully...")
        server_process.terminate()
        ngrok_process.terminate()
        server_process.wait()
        sys.exit(0)

if __name__ == "__main__":
    main()
