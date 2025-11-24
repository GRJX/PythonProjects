import json
import os
import sys

def query_data(data):
    """
    Performs custom queries on the parsed JSON data.
    Edit this function to change your query logic.
    
    Args:
        data (dict or list): The parsed JSON data.
        
    Returns:
        dict: A dictionary containing the results of the queries.
    """
    results = {}

    # Example 1: Filter a list of items
    # Assuming 'data' has a key 'users' which is a list of user objects
    if isinstance(data, dict) and 'users' in data and isinstance(data['users'], list):
        results['active_users_older_than_25'] = [
            user for user in data['users']
            if isinstance(user, dict) and user.get('age', 0) > 25 and user.get('isActive', False)
        ]

    # Example 2: Filter one layer deep - get specific top-level information
    if isinstance(data, dict):
        # Extract only specific fields from the top level
        one_layer_filter = {k: data.get(k) for k in ['name', 'version', 'description'] if k in data}
        if one_layer_filter:
            results['basic_info'] = one_layer_filter

    # Example 3: Filter nested elements
    if isinstance(data, dict) and 'products' in data and isinstance(data['products'], list):
        # Find products with price > 50
        expensive_products = [
            product for product in data['products']
            if isinstance(product, dict) and product.get('price', 0) > 50
        ]
        if expensive_products:
            results['expensive_products'] = expensive_products

    # Example 4: Find items with specific nested property
    if isinstance(data, dict) and 'items' in data and isinstance(data['items'], list):
        # Find items with a specific tag in the tags array
        tagged_items = [
            item for item in data['items']
            if isinstance(item, dict) and 
               isinstance(item.get('tags'), list) and 
               'important' in item.get('tags', [])
        ]
        if tagged_items:
            results['important_items'] = tagged_items

    # Example 5: Complex nested filtering
    if isinstance(data, dict) and 'departments' in data and isinstance(data['departments'], list):
        # Find employees in IT department with over 5 years experience
        it_experienced_employees = []
        for dept in data['departments']:
            if isinstance(dept, dict) and dept.get('name') == 'IT' and isinstance(dept.get('employees'), list):
                for employee in dept['employees']:
                    if isinstance(employee, dict) and employee.get('years_experience', 0) > 5:
                        it_experienced_employees.append(employee)
        
        if it_experienced_employees:
            results['experienced_it_staff'] = it_experienced_employees
            
    return results

def main():
    # Hardcoded parameters - edit these values directly for your needs
    input_file = "input.json"  # Default input file
    output_file = "result_query.json"  # Default output file
    print_to_stdout = False  # Set to True to print to console instead of file
    
    # Read and parse the JSON file
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at {input_file}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {input_file}")
        return
    except Exception as e:
        print(f"An unexpected error occurred while reading the file: {e}")
        return
    
    # Process the data with custom queries
    query_results = query_data(data)
    
    # Always pretty print
    formatted_output = json.dumps(query_results, indent=4)
    
    # Output results
    if print_to_stdout:
        print(formatted_output)
    else:
        try:
            # Create directory if needed
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            with open(output_file, 'w') as f:
                f.write(formatted_output)
            print(f"Results written to {output_file}")
        except Exception as e:
            print(f"Error writing to output file: {e}")
            print("Falling back to stdout:")
            print(formatted_output)

if __name__ == "__main__":
    main()
