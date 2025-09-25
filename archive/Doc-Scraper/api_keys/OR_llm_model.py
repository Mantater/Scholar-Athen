import requests
import json
import os
from dotenv import load_dotenv

def check_api_usage():
    """Check OpenRouter API key usage and limits with proper error handling."""
    
    try:
        # Load API key from .env file
        load_dotenv(dotenv_path=r"api_keys\api_key.env")
        api_key = os.getenv("OR_RPA_KEY")
        
        # Check if API key was loaded successfully
        if not api_key:
            print("❌ Error: API key not found!")
            print("Make sure your OR_RPA_KEY.env file exists and contains:")
            print(f"OR_RPA_KEY={api_key}")
            return None
        
        # Display first few characters of key for verification (security)
        print(f"🔑 Using API Key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else '****'}")
        print("📡 Checking OpenRouter API usage...")
        
        # Make the API request
        response = requests.get(
            url="https://openrouter.ai/api/v1/key",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=10  # 10 second timeout
        )
        
        # Check if request was successful
        response.raise_for_status()
        
        # Parse JSON response
        data = response.json()
        
        # Check for API errors in response
        if "error" in data:
            print(f"❌ API Error: {data['error']['message']}")
            print(f"Error Code: {data['error']['code']}")
            
            # Provide specific help based on error code
            if data['error']['code'] == 401:
                print("\n🔧 Troubleshooting Tips:")
                print("1. Verify your API key is correct")
                print("2. Check if your API key has expired")
                print("3. Ensure you're using the correct environment variable name")
                print("4. Try regenerating your API key on OpenRouter")
            
            return None
        
        # Extract usage data
        if "data" in data:
            usage_data = data["data"]
            
            print("\n✅ API Key Status: Valid")
            print("=" * 50)
            
            # Display key information
            print(f"🏷️  Label: {usage_data.get('label', 'N/A')}")
            print(f"💰 Credits Used: {usage_data.get('usage', 0):,.2f}")
            
            # Handle limit display
            limit = usage_data.get('limit')
            if limit is not None:
                print(f"🎯 Credit Limit: {limit:,.2f}")
                remaining = limit - usage_data.get('usage', 0)
                print(f"💳 Credits Remaining: {remaining:,.2f}")
                
                # Calculate usage percentage
                if limit > 0:
                    usage_percent = (usage_data.get('usage', 0) / limit) * 100
                    print(f"📊 Usage: {usage_percent:.1f}%")
                    
                    # Warn if usage is high
                    if usage_percent > 90:
                        print("⚠️  WARNING: High usage! Consider adding more credits.")
                    elif usage_percent > 75:
                        print("⚡ Notice: You've used over 75% of your credits.")
            else:
                print("🎯 Credit Limit: Unlimited")
            
            # Free tier status
            is_free = usage_data.get('is_free_tier', True)
            print(f"🆓 Free Tier: {'Yes' if is_free else 'No'}")
            
            if is_free:
                print("💡 Tip: Consider upgrading to a paid plan for higher limits and priority access.")
            
            print("=" * 50)
            
            return usage_data
        else:
            print("❌ Unexpected response format")
            print("Full response:", json.dumps(data, indent=2))
            return None
            
    except requests.exceptions.Timeout:
        print("❌ Error: Request timed out. Check your internet connection.")
        return None
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Unable to connect to OpenRouter API.")
        print("Check your internet connection and try again.")
        return None
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        print(f"Status Code: {response.status_code}")
        try:
            error_data = response.json()
            print("Error Details:", json.dumps(error_data, indent=2))
        except:
            print("Raw response:", response.text)
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {e}")
        return None
        
    except json.JSONDecodeError:
        print("❌ Error: Invalid JSON response")
        print("Raw response:", response.text)
        return None
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def main():
    """Main function to run the API checker."""
    print("=== OpenRouter API Usage Checker ===\n")
    
    usage_data = check_api_usage()
    
    if usage_data:
        print("\n✅ Check completed successfully!")
        
        # Option to save usage data to file
        save_to_file = input("\n💾 Save usage data to file? (y/N): ").strip().lower()
        if save_to_file in ['y', 'yes']:
            try:
                with open('api_usage_log.json', 'w') as f:
                    json.dump({
                        'timestamp': requests.utils.default_headers()['User-Agent'],
                        'usage_data': usage_data
                    }, f, indent=2)
                print("📁 Usage data saved to 'api_usage_log.json'")
            except Exception as e:
                print(f"❌ Failed to save file: {e}")
    else:
        print("\n❌ Check failed. Please review the errors above.")

if __name__ == "__main__":
    main()