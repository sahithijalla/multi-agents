import os
from typing import Optional, List

from tools import CalculatorTool, StringTool, WeatherTool, MathTool

# Optional backends
try:
    from groq import Groq
except Exception:
    Groq = None

try:
    from huggingface_hub import InferenceClient
except Exception:
    InferenceClient = None


# --------- Simple agents ----------
class CalculatorAgent:
    def __init__(self):
        self.tool = CalculatorTool()
    def handle(self, query: str) -> Optional[str]:
        q = query.lower()
        nums = [int(x) for x in q.replace(",", " ").split() if x.isdigit()]
        if "add" in q or "plus" in q:
            if len(nums) < 2:
                return "Please provide two numbers to add. Example: add 5 and 7"
            return str(self.tool.add(nums[0], nums[1]))
        if "multiply" in q or "times" in q:
            if len(nums) < 2:
                return "Please provide two numbers to multiply. Example: multiply 3 and 4"
            return str(self.tool.multiply(nums[0], nums[1]))
        return None

class StringAgent:
    def __init__(self):
        self.tool = StringTool()
    def handle(self, query: str) -> Optional[str]:
        q = query.lower()
        if "reverse" in q:
            text = query.lower().replace("reverse", "")
            text = query[len(query) - len(text):] if text else ""
            return self.tool.reverse(query.replace("reverse", "", 1).strip())
        if "uppercase" in q:
            return self.tool.uppercase(query.replace("uppercase", "", 1).strip())
        if "vowel count" in q:
            text = query.split("vowel count", 1)[-1].strip()
            return f"Vowel count: {self.tool.vowel_count(text)}"
        if "word count" in q or "word length" in q:
            if "word count" in q:
                text = query.split("word count", 1)[-1].strip()
            else:
                text = query.split("word length", 1)[-1].strip()
            return f"Word count: {self.tool.word_length(text)}"
        return None

class WeatherAgent:
    def __init__(self, api_key: Optional[str]):
        self.tool = WeatherTool(api_key) if api_key else None
    def handle(self, query: str) -> Optional[str]:
        if "weather" in query.lower():
            if not self.tool:
                return "Weather tool not configured."
            # detect "in <place>"
            location = "Hyderabad"
            lower = query.lower()
            if " in " in lower:
                location = query.split(" in ", 1)[-1].strip()
            return self.tool.get_weather(location)
        return None

class PrimeCheckAgent:
    def __init__(self):
        self.tool = MathTool()
    def handle(self, query: str) -> Optional[str]:
        q = query.lower()
        if "prime" in q:
            nums = [int(x) for x in q.replace(",", " ").split() if x.isdigit()]
            if not nums:
                return "Please provide a number. Example: is 29 prime?"
            n = nums[0]
            return f"{n} is prime" if self.tool.is_prime(n) else f"{n} is not prime"
        return None

class FactorialAgent:
    def __init__(self):
        self.tool = MathTool()
    def handle(self, query: str) -> Optional[str]:
        q = query.lower()
        if "factorial" in q:
            nums = [int(x) for x in q.replace(",", " ").split() if x.isdigit()]
            if not nums:
                return "Please provide a number. Example: factorial 5"
            n = nums[0]
            try:
                return f"Factorial of {n} is {self.tool.factorial(n)}"
            except Exception:
                return "Number too large for factorial."
        return None


# --------- LLM fallback with dual backend (Groq → HF) ----------
class LLMFallbackAgent:
    def __init__(self, groq_api_key: Optional[str] = None, hf_token: Optional[str] = None):
        self.groq_client = None
        self.hf_client = None

        if groq_api_key and Groq:
            try:
                self.groq_client = Groq(api_key=groq_api_key)
            except Exception:
                self.groq_client = None

        if hf_token and InferenceClient:
            try:
                # Use a chat-capable model on HF Inference
                self.hf_client = InferenceClient("mistralai/Mistral-7B-Instruct-v0.2", token=hf_token)
            except Exception:
                self.hf_client = None

    def handle(self, query: str) -> str:
        # Try Groq first (free/fast if you have a key)
        if self.groq_client:
            try:
                resp = self.groq_client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[{"role": "user", "content": query}],
                    temperature=0.7,
                    max_tokens=300,
                )
                return resp.choices[0].message.content.strip()
            except Exception as e:
                # fall through to HF
                pass

        # Then try Hugging Face chat
        if self.hf_client:
            try:
                resp = self.hf_client.chat_completion(
                    model="mistralai/Mistral-7B-Instruct-v0.2",
                    messages=[{"role": "user", "content": query}],
                    temperature=0.7,
                    max_tokens=300,
                )
                return resp.choices[0].message["content"].strip()
            except Exception as e:
                # Special-case 402
                msg = str(e)
                if "402" in msg or "Payment Required" in msg:
                    return ("LLM fallback unavailable: Hugging Face Inference credits exhausted. "
                            "Add a GROQ_API_KEY in Streamlit secrets to enable Groq fallback, "
                            "or upgrade HF plan.")
                return f"LLM error: {msg}"

        return ("LLM fallback not configured 🤖. "
                "Add GROQ_API_KEY or HF_TOKEN in .streamlit/secrets.toml.")

# --------- Router ----------
class MasterAgent:
    def __init__(self, weather_api_key: Optional[str] = None, hf_token: Optional[str] = None, groq_api_key: Optional[str] = None):
        self.agents: List = [
            CalculatorAgent(),
            StringAgent(),
            WeatherAgent(weather_api_key),
            PrimeCheckAgent(),
            FactorialAgent(),
        ]
        self.llm = LLMFallbackAgent(groq_api_key=groq_api_key, hf_token=hf_token)

    def route(self, query: str) -> str:
        for agent in self.agents:
            try:
                result = agent.handle(query)
            except Exception as e:
                result = f"Tool error: {e}"
            if result:
                return result
        return self.llm.handle(query)
