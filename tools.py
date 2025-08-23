import math
import requests

class CalculatorTool:
    def add(self, a, b):
        return a + b
    def multiply(self, a, b):
        return a * b

class StringTool:
    def reverse(self, text):
        return text[::-1]
    def uppercase(self, text):
        return text.upper()
    def vowel_count(self, text):
        vowels = "aeiouAEIOU"
        return sum(1 for ch in text if ch in vowels)
    def word_length(self, text):
        words = [w for w in text.split() if w.strip()]
        return len(words)

class MathTool:
    def is_prime(self, n):
        if n < 2:
            return False
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                return False
        return True
    def factorial(self, n):
        return math.factorial(n)

class WeatherTool:
    def __init__(self, api_key):
        self.api_key = api_key
        self.url = "https://api.tomorrow.io/v4/weather/realtime"
    def get_weather(self, location="Hyderabad"):
        try:
            params = {"location": location, "apikey": self.api_key}
            r = requests.get(self.url, params=params, timeout=10)
            if r.status_code != 200:
                return "Weather service unavailable."
            data = r.json()
            vals = data.get("data", {}).get("values", {})
            temp = vals.get("temperature")
            code = vals.get("weatherCode")
            if temp is None or code is None:
                return "Weather data incomplete."
            return f"The weather in {location} is {code} with {temp}°C."
        except Exception:
            return "Weather service unavailable."
