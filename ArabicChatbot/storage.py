"""
Storage Module for Arabic Learning Chatbot
Handles loading and saving of conversation data
"""
import json
import os

RESPONSES_FILE = "responses.json"

def initialize():
    """Initialize the storage by creating the responses file if it doesn't exist."""
    if not os.path.exists(RESPONSES_FILE):
        with open(RESPONSES_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False)

def get_responses():
    """
    Load responses from the JSON file.
    
    Returns:
        dict: A dictionary of message-response pairs
    """
    try:
        with open(RESPONSES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        # If there's an error loading the file, return an empty dict
        return {}

def save_responses(responses):
    """
    Save responses to the JSON file.
    
    Args:
        responses (dict): A dictionary of message-response pairs
    """
    with open(RESPONSES_FILE, "w", encoding="utf-8") as f:
        json.dump(responses, f, ensure_ascii=False, indent=2)

def get_conversation_history(limit=10):
    """
    Get the most recent conversation exchanges.
    
    Args:
        limit (int): Maximum number of exchanges to return
        
    Returns:
        list: A list of the most recent exchanges
    """
    # This is a placeholder. In a more advanced implementation,
    # we would store conversation history separately.
    responses = get_responses()
    history = []
    for message, response in list(responses.items())[-limit:]:
        history.append({"message": message, "response": response})
    return history

def clear_responses():
    """Clear all stored responses (for testing or reset purposes)."""
    save_responses({})
