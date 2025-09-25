import requests
import os
import json
from dotenv import load_dotenv
import re

# -----------------------------
# Config
# -----------------------------
load_dotenv(dotenv_path=r"api_keys\api_key.env")
API_KEY = os.getenv("OR_RPA_KEY")

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "nvidia/nemotron-nano-9b-v2:free"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# -----------------------------
# Calling the LLM API
# -----------------------------
def call_llm(prompt: str) -> str:
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
# Extracting keywords and summaries
# -----------------------------
def extract_keywords_and_summary(paragraphs: list[str], get_summary: bool = True, retry_on_fail: bool = True):
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

        llm_text = call_llm(prompt)
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
                llm_text = call_llm(prompt_retry)
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
            sentences = paragraph.split(".")
            keywords_per_paragraph[idx] = [s.strip().split()[0] for s in sentences if s.strip() != ""][:8]
            if get_summary:
                summary_per_paragraph[idx] = sentences[0].strip() if sentences else None

    return keywords_per_paragraph, summary_per_paragraph


# -----------------------------
# Rank Keywords by Relevance (LLM)
# -----------------------------
def rank_keywords_llm(paragraph: str, keywords: list[str]) -> list[tuple[str, float | None]]:
    """
    Ranks keywords by their relevance to a paragraph using an LLM.

    Parameters:
        paragraph (str): The paragraph text for context.
        keywords (list[str]): The list of extracted keywords.

    Returns:
        list[tuple[str, float | None]]: Ranked keywords with relevance scores.
            If parsing fails, relevance is returned as None.
    """
    prompt = f"""
    Rank the following keywords by their relevance to the paragraph.

    Paragraph:
    {paragraph}

    Keywords:
    {keywords}

    Respond ONLY in JSON with this format:
    {{
        "ranked_keywords": [
            {{"keyword": "example", "relevance": 0.95}},
            {{"keyword": "example2", "relevance": 0.85}}
        ]
    }}
    """

    llm_text = call_llm(prompt)
    llm_text_clean = re.sub(r"```json|```", "", llm_text, flags=re.IGNORECASE).strip()

    try:
        llm_json = json.loads(llm_text_clean)
        ranked = [(kw["keyword"], kw["relevance"]) for kw in llm_json["ranked_keywords"]]
        return ranked
    except json.JSONDecodeError:
        print("⚠️ Failed to parse JSON. Returning unranked keywords.")
        return [(kw, None) for kw in keywords]


# -----------------------------
# Main test
# -----------------------------
if __name__ == "__main__":
    cleaned_paragraphs = [
        "Recent advances in natural language processing have enabled machines to understand and generate human-like text. Transformer architectures like GPT and BERT have been instrumental in achieving state-of-the-art results in many NLP tasks.",
        "Climate change is causing significant shifts in weather patterns across the globe, leading to increased frequency of extreme events like hurricanes, floods, and droughts. Understanding these patterns is critical for mitigation and adaptation strategies.",
        "Quantum computing has the potential to solve certain computational problems exponentially faster than classical computers. Research is focused on building stable qubits and error-correction techniques."
    ]

    # Step 1: Extract
    keywords, summaries = extract_keywords_and_summary(cleaned_paragraphs)

    print("\nKeywords per paragraph:")
    for idx, kw in keywords.items():
        print(f"Paragraph {idx}: {kw}")

    print("\nSummaries per paragraph:")
    for idx, summary in summaries.items():
        print(f"Paragraph {idx}: {summary}")

    # Step 1b: Rank
    print("\nRanked Keywords per paragraph:")
    for idx, paragraph in enumerate(cleaned_paragraphs):
        if keywords[idx]:
            ranked = rank_keywords_llm(paragraph, keywords[idx])
            print(f"Paragraph {idx}: {ranked}")
