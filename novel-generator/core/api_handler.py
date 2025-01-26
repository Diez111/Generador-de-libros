import requests
import time
import random
import socket
import regex
import json
from typing import Optional, Dict

class AdvancedAPIHandler:
    def __init__(self, api_key: str):
        self.API_KEY = api_key
        self.BASE_URL = "https://api.deepseek.com/v1/chat/completions"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "NovelGeneratorPro/5.1"
        })
        self.request_counter = 0
        self.last_request_time = time.time()
        self.retry_delay = 1
    
    def check_internet(self, retries=3) -> bool:
        for i in range(retries):
            try:
                socket.create_connection(("8.8.8.8", 53), timeout=2+i*2)
                return True
            except OSError:
                time.sleep(1)
        return False

    def query(self, prompt: str, system_message: str = "", context: str = "", 
             temp: float = 0.7, max_tokens: int = 4000, retries: int = 5) -> Optional[str]:
        
        self._rate_limit()
        full_context = f"CONTEXTO PREVIO:\n{context}\n\nPROMPT ACTUAL:\n{prompt}"
        
        for attempt in range(retries):
            try:
                messages = [{"role": "user", "content": full_context}]
                if system_message:
                    messages.insert(0, {"role": "system", "content": system_message})
                
                response = self.session.post(
                    self.BASE_URL,
                    json={
                        "model": "deepseek-chat",
                        "messages": messages,
                        "temperature": temp,
                        "max_tokens": max_tokens,
                        "top_p": 0.95,
                        "frequency_penalty": 0.2
                    },
                    timeout=90
                )
                
                response.raise_for_status()
                raw_content = response.json()['choices'][0]['message']['content'].strip()
                return self.sanitize_content(raw_content)
            
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    retry_after = int(e.response.headers.get('Retry-After', 15)) + random.randint(1, 5)
                    print(f"⏳ Rate limit alcanzado. Esperando {retry_after} segundos...")
                    time.sleep(retry_after)
                    self.retry_delay *= 1.5
                else:
                    print(f"⚠️ Error HTTP {e.response.status_code}: {e.response.text}")
                    raise
            except requests.exceptions.RequestException as e:
                backoff = self.retry_delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"⚠️ Error de conexión. Reintento {attempt+1}/{retries} en {backoff:.1f}s")
                time.sleep(backoff)
        
        raise Exception("Error tras reintentos")

    def _rate_limit(self):
        now = time.time()
        elapsed = now - self.last_request_time
        
        if self.request_counter >= 5 and elapsed < 60:
            sleep_time = 60 - elapsed
            print(f"⏳ Respeta límite de tasa. Esperando {sleep_time:.1f} segundos...")
            time.sleep(sleep_time)
            self.request_counter = 0
            self.last_request_time = now
        else:
            if elapsed > 60:
                self.request_counter = 0
            self.request_counter += 1
            self.last_request_time = now

    @staticmethod
    def sanitize_content(text: str) -> str:
        text = regex.sub(r'[#*`]', '', text)
        text = regex.sub(r'\n{3,}', '\n\n', text)
        text = regex.sub(r'\u2028', '\n', text)
        return text.strip()

    def safe_json_extract(self, text: str) -> Optional[dict]:
        text = text.replace('\\"', "'").replace('\\n', ' ')
        text = regex.sub(r'(?<!\\)\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', r'', text)
        
        json_pattern = r'(?s)(?:```(?:json)?\n?)?(\{(?:[^{}]|(?R))*+\})(?:```)?'
        matches = regex.finditer(json_pattern, text, regex.DOTALL)
        
        for match in matches:
            try:
                cleaned = match.group(1).strip()
                parsed = json.loads(cleaned)
                if isinstance(parsed, dict) and len(parsed) > 0:
                    return parsed
            except json.JSONDecodeError:
                continue
        
        try:
            stack = []
            start = end = -1
            for i, c in enumerate(text):
                if c == '{':
                    if not stack:
                        start = i
                    stack.append(c)
                elif c == '}':
                    if stack:
                        stack.pop()
                        if not stack:
                            end = i + 1
                            break
            if start != -1 and end != -1:
                return json.loads(text[start:end])
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {str(e)}")
            return None