import datetime
from google import genai
from google.genai import types

class SamRouter:
    def __init__(self):
        self.client = genai.Client()
        self.model_name = "gemini-3.8-flash"
        
    def get_chat_session(self):
        current_time = datetime.datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        system_prompt = (
            f"You are Sam, a modular AI assistant designed to help manage Linux and Android "
            f"tasks on a Chromebook. The current date and time is {current_time}."
        )
        
        return self.client.chats.create(
            model=self.model_name,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7,
            )
        )
