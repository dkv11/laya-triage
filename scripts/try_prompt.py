import os

from dotenv import load_dotenv
from openai import OpenAI

from app.prompts import build_extract_prompt

load_dotenv()
client = OpenAI(base_url=os.environ["LLM_BASE_URL"], api_key=os.environ["OPENROUTER_API_KEY"])

MESSAGES = [
    "P-101 se bahut awaaz aa rahi hai aur garam bhi ho raha hai",
    "motor se jalne ki smell aa rahi hai",
    "flow meter 2 ghante se same reading dikha raha hai",
    "blower trip ho gaya, MCB gir gaya",
    "pump ke neeche paani leak ho raha hai",
    "sab theek hai, routine round done",
    "पंप से बहुत आवाज़ आ रही है",

]

system_prompt = build_extract_prompt()

for text in MESSAGES:
    response = client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
    )
    print(f"\n>>> {text}")
    print(response.choices[0].message.content)
