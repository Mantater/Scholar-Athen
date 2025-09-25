import requests
import json
import re
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=r"api_keys\api_key.env")
API_KEY = os.getenv("OR_RPA_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "nvidia/nemotron-nano-9b-v2:free"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

class LLMClient:
    def call(self, prompt: str) -> str:
        data = {"model": MODEL_NAME, "messages": [{"role": "user", "content": prompt}]}
        resp = requests.post(API_URL, headers=HEADERS, json=data)
        return resp.json()["choices"][0]["message"]["content"].strip()

    def extract_keywords_and_summary(self, paragraphs, get_summary=True):
        keywords, summaries = {}, {} if get_summary else None
        for idx, para in enumerate(paragraphs):
            prompt = f"""
            Extract keywords and {'a summary' if get_summary else ''} from the paragraph below.
            Respond ONLY in JSON:
            {{
                "keywords": ["keyword1", "keyword2"],
                "summary": "short summary"
            }}
            Paragraph:
            {para}
            """
            text = self.call(prompt)
            text_clean = re.sub(r"```json|```", "", text, flags=re.IGNORECASE).strip()
            try:
                data = json.loads(text_clean)
                keywords[idx] = data.get("keywords", [])
                if get_summary:
                    summaries[idx] = data.get("summary", None)
            except json.JSONDecodeError:
                keywords[idx] = []
                if get_summary:
                    summaries[idx] = ""
        return keywords, summaries

    def rank_keywords(self, paragraph, keywords):
        prompt = f"""
        Rank these keywords by relevance to paragraph:
        Paragraph: {paragraph}
        Keywords: {keywords}
        Respond ONLY in JSON with: {{"ranked_keywords":[{{"keyword":"example","relevance":0.9}}]}}
        """
        text = self.call(prompt)
        text_clean = re.sub(r"```json|```", "", text, flags=re.IGNORECASE).strip()
        try:
            data = json.loads(text_clean)
            return [(kw["keyword"], kw["relevance"]) for kw in data["ranked_keywords"]]
        except:
            return [(kw, None) for kw in keywords]
