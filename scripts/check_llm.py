import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.getenv("LLM_BASE_URL"),
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

response = client.chat.completions.create(
    model=os.getenv("LLM_MODEL"),
    messages=[
        {"role": "system", "content": "You are a maintenance assistant at an industrial plant. Answer in 2 short sentences."},
        {"role": "user", "content": "motor se jalne ki smell aa rahi hai, kya karu?"},
    ],
)

print(response.choices[0].message.content)
print("Model used:", response.model)
print("Total tokens used:", response.usage.total_tokens)