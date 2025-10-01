from flask import Flask, request, jsonify
import requests
import logging

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self, verify_token, access_token):
        self.verify_token = verify_token
        self.access_token = access_token
        self.api_url = f"https://graph.facebook.com/v17.0/"

    def verify_webhook(self, mode, token, challenge):
        if mode and token:
            if mode == "subscribe" and token == self.verify_token:
                return challenge
        return None

    def process_message(self, message):
        # Extract message text
        message_text = message.get('text', {}).get('body', '')
        
        # Call chatbot API
        response = requests.post(
            "http://localhost:8000/api/chat",
            json={"message": message_text, "session_id": "whatsapp_user"}
        )
        
        if response.status_code == 200:
            return response.json()["response"]
        else:
            return "Sorry, I'm having trouble processing your message."

    def send_message(self, phone_number, message):
        url = f"{self.api_url}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "text": {"body": message}
        }
        
        response = requests.post(url, headers=headers, json=payload)
        return response.json()