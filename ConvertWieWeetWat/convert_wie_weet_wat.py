import pandas as pd

# Load the Excel file
excel_file = '/Users/jelle/Library/Mobile Documents/com~apple~CloudDocs/Documents/Professional/Newspark/Hackaton/WieWeetWat.xlsx'
xl = pd.ExcelFile(excel_file)

# Read the 'CurrentWWW' sheet
df_current = xl.parse('CurrentWWW')

# Prepare the dataframes for each table/entity
df_categories = pd.DataFrame(columns=['Id', 'Name'])
df_subcategories = pd.DataFrame(columns=['Id', 'Name', 'CategoryId'])
df_persons = pd.DataFrame(columns=['Id', 'Name', 'Email'])
df_person_knowledge = pd.DataFrame(columns=['Id', 'PersonId', 'SubCategoryId', 'KnowledgeLevel', 'IsInterested'])

# Dictionaries to store generated IDs
category_ids = {}
subcategory_ids = {}
person_ids = {}
knowledge_id = 1

# Identify person columns (dynamic)
person_columns = df_current.columns[3:]

# Process each row in the dataframe
for index, row in df_current.iterrows():
    # Handle Category
    if pd.notnull(row['Category']):
        category_name = str(row['Category']).strip()
    if category_name not in category_ids:
        category_ids[category_name] = len(category_ids) + 1
        df_categories = df_categories.append({'Id': category_ids[category_name], 'Name': category_name}, ignore_index=True)

    # Handle SubCategory
    if pd.notnull(row['SubCategory']):
        subcategory_name = str(row['SubCategory']).strip()
    if subcategory_name not in subcategory_ids:
        subcategory_ids[subcategory_name] = len(subcategory_ids) + 1
        df_subcategories = df_subcategories.append({
            'Id': subcategory_ids[subcategory_name],
            'Name': subcategory_name,
            'CategoryId': category_ids[category_name]
        }, ignore_index=True)

    # Handle Persons and their Knowledge
    for person_column in person_columns:
        person_name = person_column.strip()
        knowledge_info = row[person_column]
        
        if pd.notna(knowledge_info):
            knowledge_info = str(knowledge_info).strip()
            knowledge_level = 0
            is_interested = False

            # Check if 'int' is part of the knowledge indicating interest
            if 'int' in knowledge_info.lower():
                is_interested = True
                knowledge_info = knowledge_info.replace('int', '').strip()

            # Convert the remaining knowledge information to integer if possible
            if knowledge_info.isdigit():
                knowledge_level = int(knowledge_info)
            
            # Add new person if not already in the dictionary
            if person_name not in person_ids:
                person_ids[person_name] = len(person_ids) + 1
                df_persons = df_persons.append({
                    'Id': person_ids[person_name],
                    'Name': person_name,
                    'Email': f'{person_name.lower()}@example.com'
                }, ignore_index=True)
            
            # Append to PersonSubCategoryKnowledge
            df_person_knowledge = df_person_knowledge.append({
                'Id': knowledge_id,
                'PersonId': person_ids[person_name],
                'SubCategoryId': subcategory_ids[subcategory_name],
                'KnowledgeLevel': knowledge_level,
                'IsInterested': is_interested
            }, ignore_index=True)
            knowledge_id += 1

# Write the new dataframes to their respective sheets in the Excel file
with pd.ExcelWriter(excel_file, engine='openpyxl', mode='a') as writer: 
    df_categories.to_excel(writer, sheet_name='Category', index=False)
    df_subcategories.to_excel(writer, sheet_name='SubCategory', index=False)
    df_persons.to_excel(writer, sheet_name='Person', index=False)
    df_person_knowledge.to_excel(writer, sheet_name='PersonSubCategoryKnowledge', index=False)

print("Conversion complete and data is saved in the Excel file.")
