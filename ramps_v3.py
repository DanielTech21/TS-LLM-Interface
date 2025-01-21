# Imports required modules
import re  # Regular expression module for text processing
import requests  # HTTP requests module for API calls
from datetime import datetime  # Module for handling dates and timestamps
import csv  # Module for writing to CSV files

# INTERCOM_PROD_KEY = ''

# Removes HTML tags from a given text
def remove_html_tags(text):
    clean = re.sub(r'<.*?>', '', text)  # Uses a regex to replace HTML tags with an empty string
    return clean

# Fetches a specific Intercom conversation based on the conversation ID
def get_intercom_conversation(conversation_id):
    url = f'https://api.intercom.io/conversations/{conversation_id}'  # Constructs the API endpoint URL
    response = requests.get(url, headers={"Authorization": f"Bearer {INTERCOM_PROD_KEY}"})  # Sends GET request with API key
    
    if response.status_code != 200:  # Checks if the response indicates an error
        print('Status:', response.status_code, 'Problem while looking for ticket status')
        print('Error: ', response.json())  # Logs the error message from the response
        return None
    ticket = response.json()  # Parses the JSON response
    return ticket

# Extracts the summary of a conversation by looking for a specific part type
def get_conversation_summary(conversation):
    if 'conversation_parts' in conversation:  # Checks if conversation parts exist
        conversation_parts = conversation['conversation_parts'].get('conversation_parts', None)
        for part in conversation_parts:  # Iterates through all parts
            part_type = part['part_type']
            if part_type == 'conversation_summary':  # Checks for the specific part type
                return remove_html_tags(part['body'])  # Removes HTML tags from the summary
    return None

# Extracts a transcript of the conversation
def get_conversation_transcript(conversation):
    transcript = ''
    if 'conversation_parts' in conversation:  # Checks if conversation parts exist
        conversation_parts = conversation['conversation_parts'].get('conversation_parts', None)
        for part in conversation_parts:  # Iterates through conversation parts
            part_type = part['part_type']
            if part_type == 'comment':  # Checks for comment type
                author = part['author']['type']  # Gets the author and type
                comment = remove_html_tags(part['body'])  # Removes HTML tags from the comment
                transcript += f"{author}: {comment}\n"  # Appends the formatted comment to the transcript
    return transcript

# Retrieves the customer satisfaction (CSAT) remark from a conversation
def get_conversation_csat_remark(conversation):
    csat = conversation.get('conversation_rating')  # Fetches the CSAT data
    if not csat:  # If no CSAT data, return None
        return None
    remark = csat.get('remark', '')  # Extracts the CSAT remark
    return remark

# Searches for conversations within a specific date range
def search_conversations(start_date_str, end_date_str):
    # Converts date strings to UNIX timestamps
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").timestamp()
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").timestamp()
    
    url = "https://api.intercom.io/conversations/search"  # API endpoint for searching conversations
    headers = {  # API request headers
        "Authorization": f"Bearer {INTERCOM_PROD_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    payload = {  # Search query payload
        "query": {
            "operator": "AND",
            "value": [
                {
                    "field": "statistics.last_close_at",
                    "operator": ">",
                    "value": int(start_date)
                },
                {
                    "field": "statistics.last_close_at",
                    "operator": "<",
                    "value": int(end_date)
                }
            ]
        },
        "pagination": {
            "per_page": 150
        }
    }

    all_conversations = []  # List to store retrieved conversations
    next_page = None  # Tracks pagination

    while True:  # Loop to handle pagination
        response = requests.post(url, headers=headers, json=payload)  # Sends POST request
        print(len(all_conversations))  # Logs the number of conversations retrieved so far

        if response.status_code == 200:  # Checks for successful response
            data = response.json()  # Parses JSON response
            all_conversations.extend(data.get('conversations', []))  # Appends conversations to the list
            
            pagination = data.get('pages', {})
            next_page_data = pagination.get('next', None)

            if next_page_data and 'starting_after' in next_page_data:  # Handles pagination
                next_page = next_page_data['starting_after']
                payload['pagination']['starting_after'] = next_page
            else:
                break
            
        else:  # Logs the error and terminates
            print(f"Error: {response.status_code} - {response.text}")
            return None

    return all_conversations

# Filters conversations based on a product attribute and buy/sell flag
def filter_conversations_by_product(conversations, product):
    filtered_conversations_buy = []  # Stores buy-related conversations
    filtered_conversations_sell = []  # Stores sell-related conversations
    for conversation in conversations:  # Iterates through each conversation
        attributes = conversation['custom_attributes']  # Fetches custom attributes
        if 'MetaMask area' in attributes and 'Buy or Sell' in attributes:
            if attributes['MetaMask area'] == product:
                if attributes['Buy or Sell'] == 'Sell':  # Filters for sell
                    filtered_conversations_sell.append(get_intercom_conversation(conversation['id']))
                elif attributes['Buy or Sell'] == 'Buy':  # Filters for buy
                    filtered_conversations_buy.append(get_intercom_conversation(conversation['id']))
    return filtered_conversations_buy, filtered_conversations_sell

# Stores conversation data to a CSV file
def store_conversations_to_csv(conversations, file_path):
    headers = ['conversation_id', 'summary']  # Specifies CSV headers

    with open(file_path, mode='w', newline='') as file:  # Opens the file in write mode
        writer = csv.DictWriter(file, fieldnames=headers)  # Initializes CSV writer
        writer.writeheader()  # Writes the header row

        for conversation in conversations:  # Iterates through conversations
            conversation_id = conversation['id']  # Extracts conversation ID
            summary = get_conversation_summary(conversation)  # Gets the summary

            writer.writerow({  # Writes data row
                'conversation_id': conversation_id,
                'summary': summary
            })

# Main function orchestrating the process
def main_function():
    conversations = search_conversations("2024-11-11", "2024-11-18")  # Searches based on date for conversations
    if conversations:  # If conversations are found
        filtered_conversations_buy, filtered_conversations_sell = filter_conversations_by_product(conversations, 'Ramps')
        print(len(filtered_conversations_buy))  # Logs the number of buy conversations
        print(len(filtered_conversations_sell))  # Logs the number of sell conversations
        store_conversations_to_csv(filtered_conversations_buy, 'onRamp_11_17_Nov.csv')  # Stores buy conversations to CSV
        store_conversations_to_csv(filtered_conversations_sell, 'offRamp_11_17_Nov.csv')  # Stores sell conversations to CSV
    else:  # If no conversations are found
        print('No conversations found for provided timeframe')

# Entry point of the script
main_function()

#ticket = get_intercom_conversation(505032)
#print(ticket['statistics']['last_close_at'])
# print(get_conversation_transcript(ticket))
# print(get_conversation_csat_remark(ticket))
# print(get_conversation_summary(ticket))
