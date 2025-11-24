#!/usr/bin/env python3
"""
CLI for interacting with Notion databases.
"""

import os
import requests
from pathlib import Path
from notion_client import NotionClient
from dotenv import load_dotenv

# Load environment variables from .env file
# Get the directory where this script is located
script_dir = Path(__file__).parent
env_path = script_dir / '.env'
load_dotenv(dotenv_path=env_path)

def main():
    """Main CLI function to demonstrate NotionClient usage."""
    # Get NOTION token from environment
    NOTION_TOKEN = os.getenv('NOTION_TOKEN')
    # Get database ID from environment
    DATABASE_ID = os.getenv('NOTION_DATABASE_ID')

    try:
        print("🔧 Initializing Notion client...")
        client = NotionClient(NOTION_TOKEN)
    
        print("\n=== Getting Database Entries ===")
        database_obj = client.get_database_entries(DATABASE_ID)
        data_source_id = database_obj.get("data_sources")[0].get("id")
        all_pages = client.get_all_data_source_pages(data_source_id)
        
        for page in all_pages:
            page_obj = client.get_page(page.get("id"))
            
        print("\n✅ All operations completed successfully!")
        
    except ValueError as e:
        print(f"\n❌ Configuration error: {e}")
        print("   Make sure NOTION_TOKEN is set in your .env file")
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ API error: {e}")
        if hasattr(e, 'response'):
            print(f"   Response: {e.response.text}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
