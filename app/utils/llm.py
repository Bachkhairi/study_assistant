import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

class GroqModel:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model_name = os.getenv("GROQ_MODEL_NAME")
        if not self.api_key:
            raise ValueError("Missing GROQ_API_KEY in environment variables.")

        self.client = Groq(api_key=self.api_key)

    def chat_completion(self, messages: list[dict[str, str]]) -> str:
        """
        Send chat messages to the Groq LLM and return the response content.

        Args:
            messages (list): A list of messages like:
                [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]

        Returns:
            str: The generated response.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[GroqModel] Error: {e}")
            return ""
