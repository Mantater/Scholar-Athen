import requests
import os
import json
from dotenv import load_dotenv
import re

# -----------------------------
# Config
# -----------------------------
load_dotenv(dotenv_path="OR_RPA_KEY.env")
API_KEY = os.getenv("ResearchPaper_API_KEY")

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "nvidia/nemotron-nano-9b-v2:free"

# -----------------------------
# Calling the LLM API
# -----------------------------
def call_llm(prompt, headers):
    """
    Sends a prompt to the LLM model and retrieves the response text.

    Parameters:
        prompt (str): The input text prompt to send to the LLM.

    Returns:
        str: The LLM response content as a string.
    """
    data = {"model": MODEL_NAME, "messages": [{"role": "user", "content": prompt}]}
    response = requests.post(API_URL, headers=headers, json=data)
    response_json = response.json()
    llm_text = response_json["choices"][0]["message"]["content"].strip()
    return llm_text

# -----------------------------
# Extracting keywords and summaries from paragraphs
# -----------------------------
def extract_keywords_and_summary(paragraphs, get_summary=True, retry_on_fail=True):
    """
    Extracts keywords and optional summaries from a list of paragraphs using an LLM.
    Returns dictionaries mapping paragraph indices to extracted values.

    Parameters:
        paragraphs (list[str]): List of paragraph strings to process.
        get_summary (bool, optional): Whether to generate summaries. Default is True.
        retry_on_fail (bool, optional): Retry once with stricter prompt if JSON parsing fails. Default is True.

    Returns:
        tuple:
            dict[int, list[str]]: Keywords per paragraph, keyed by paragraph index.
            dict[int, str] | None: Summaries per paragraph, or None if get_summary is False.
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    keywords_per_paragraph = {}
    summary_per_paragraph = {} if get_summary else None

    for idx, paragraph in enumerate(paragraphs):
        prompt = f"""
        Extract keywords and {'a summary' if get_summary else ''} from the paragraph below.
        Respond ONLY in valid JSON inside a ```json ... ``` code block, with this structure:

        {{
            "keywords": ["keyword1", "keyword2", ...],
            "summary": "short summary here"
        }}

        Paragraph:
        {paragraph}
        """

        llm_text = call_llm(prompt, headers)

        # Remove code block markers if present
        llm_text_clean = re.sub(r"```json|```", "", llm_text, flags=re.IGNORECASE).strip()

        try:
            llm_json = json.loads(llm_text_clean)
            keywords_per_paragraph[idx] = llm_json.get("keywords", [])
            if get_summary:
                summary_per_paragraph[idx] = llm_json.get("summary", None)
        except json.JSONDecodeError:
            # Retry once if enabled
            if retry_on_fail:
                print(f"Retrying paragraph {idx} with stricter prompt...")
                prompt_retry = f"""
                RESPOND ONLY in JSON, STRICTLY following this format (no extra text):

                {{
                    "keywords": ["keyword1", "keyword2", ...],
                    "summary": "short summary here"
                }}

                Paragraph:
                {paragraph}
                """
                llm_text = call_llm()
                llm_text_clean = re.sub(r"```json|```", "", llm_text, flags=re.IGNORECASE).strip()
                try:
                    llm_json = json.loads(llm_text_clean)
                    keywords_per_paragraph[idx] = llm_json.get("keywords", [])
                    if get_summary:
                        summary_per_paragraph[idx] = llm_json.get("summary", None)
                    continue
                except json.JSONDecodeError:
                    pass

            # Fallback heuristic parsing
            print(f"Warning: Failed to parse JSON for paragraph {idx}, using heuristic fallback.")
            # Simple fallback: split by sentences and pick nouns / phrases (basic)
            sentences = paragraph.split(".")
            keywords_per_paragraph[idx] = [s.strip().split()[0] for s in sentences if s.strip() != ""][:8]  # up to 8 words
            if get_summary:
                summary_per_paragraph[idx] = sentences[0].strip() if sentences else None

    return keywords_per_paragraph, summary_per_paragraph

# -----------------------------
# Main test
# -----------------------------
if __name__ == "__main__":
    cleaned_paragraphs = [
        "Recent advances in natural language processing have enabled machines to understand and generate human-like text. Transformer architectures like GPT and BERT have been instrumental in achieving state-of-the-art results in many NLP tasks.",
        "Climate change is causing significant shifts in weather patterns across the globe, leading to increased frequency of extreme events like hurricanes, floods, and droughts. Understanding these patterns is critical for mitigation and adaptation strategies.",
        "Quantum computing has the potential to solve certain computational problems exponentially faster than classical computers. Research is focused on building stable qubits and error-correction techniques."
    ]

    keywords, summaries = extract_keywords_and_summary(cleaned_paragraphs)

    print("\nKeywords per paragraph:")
    for idx, kw in keywords.items():
        print(f"Paragraph {idx}: {kw}")

    print("\nSummaries per paragraph:")
    for idx, summary in summaries.items():
        print(f"Paragraph {idx}: {summary}")
