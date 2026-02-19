import ollama
import json
from typing import Dict, Any, Optional

def get_diagnosis(system_prompt: str, user_message: str, model: str = "qwen2.5:3b") -> Optional[Dict[str, Any]]:
    """
    Communicates with Ollama to get a structured JSON diagnosis.
    """
    try:
        response = ollama.chat(
            model=model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message},
            ],
            format='json'
        )
        
        content = response['message']['content']
        # The ollama library might return a string or already parsed dict depending on version
        if isinstance(content, str):
            return json.loads(content)
        return content
    except Exception as e:
        print(f"Error communicating with LLM: {e}")
        return None
