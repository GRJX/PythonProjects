import os
import requests
from typing import Dict, Any, List, Optional


class NotionClient:
    """
    A simplified client for interacting with the Notion API.
    
    Supports:
    - Getting database entries
    - Retrieving page details
    - Updating page content
    - Updating page properties
    
    Reference: https://developers.notion.com/reference/intro
    """

    BASE_URL = "https://api.notion.com/v1"
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize the Notion client.
        
        Args:
            token: Notion API token (if not provided, uses NOTION_TOKEN env variable)
            
        Raises:
            ValueError: If no token is provided or found in environment
        """
        self.token = token
        if not self.token:
            raise ValueError("Notion token must be provided or set in NOTION_TOKEN environment variable")
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2025-09-03",
            "Content-Type": "application/json"
        }
    
    def get_database_entries(self, database_id: str) -> List[Dict[str, Any]]:
        """
        Get all entries (pages) from a database.
        Automatically handles pagination to retrieve all results.
        
        Args:
            database_id: The ID of the database
        
        Returns:
            List of all page objects from the database
        """
        url = f"{self.BASE_URL}/databases/{database_id}"
            
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_page(self, page_id: str) -> Dict[str, Any]:
        """
        Retrieve a page by its ID.
        
        Args:
            page_id: The ID of the page to retrieve
        
        Returns:
            Page object containing properties and metadata
            
        Raises:
            requests.exceptions.HTTPError: If the API request fails
            
        Reference: https://developers.notion.com/reference/retrieve-a-page
        """
        url = f"{self.BASE_URL}/pages/{page_id}"
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_data_sources(self, data_source_id: str, filter_conditions: Optional[Dict[str, Any]] = None, 
                        sorts: Optional[List[Dict[str, Any]]] = None, 
                        start_cursor: Optional[str] = None,
                        page_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Query a data source to get a list of pages with optional filtering and sorting.
        
        Args:
            data_source_id: The ID of the data source
            filter_conditions: Optional filter object to apply to the query
            sorts: Optional list of sort objects to order results
            start_cursor: Optional cursor for pagination (to get next page of results)
            page_size: Optional number of results to return (max 100)
        
        Returns:
            Dictionary containing:
                - results: List of page objects
                - next_cursor: Cursor for next page (None if no more results)
                - has_more: Boolean indicating if more results exist
                
        Raises:
            requests.exceptions.HTTPError: If the API request fails
            
        Reference: https://developers.notion.com/reference/query-a-data-source
        """
        url = f"{self.BASE_URL}/data_sources/{data_source_id}/query"
        
        payload = {}
        if filter_conditions:
            payload["filter"] = filter_conditions
        if sorts:
            payload["sorts"] = sorts
        if start_cursor:
            payload["start_cursor"] = start_cursor
        if page_size:
            payload["page_size"] = min(page_size, 100)  # Max is 100
            
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_all_data_source_pages(self, data_source_id: str, 
                                   filter_conditions: Optional[Dict[str, Any]] = None,
                                   sorts: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Get all pages from a data source, automatically handling pagination.
        
        Args:
            data_source_id: The ID of the data source
            filter_conditions: Optional filter object to apply to the query
            sorts: Optional list of sort objects to order results
        
        Returns:
            List of all page objects from the data source
            
        Raises:
            requests.exceptions.HTTPError: If the API request fails
        """
        all_pages = []
        start_cursor = None
        has_more = True
        
        while has_more:
            response = self.get_data_sources(
                data_source_id=data_source_id,
                filter_conditions=filter_conditions,
                sorts=sorts,
                start_cursor=start_cursor
            )
            
            all_pages.extend(response.get("results", []))
            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")
        
        return all_pages