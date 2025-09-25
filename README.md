# Scholar Athen

## Description
Scholar Athen is a research assistant tool designed to help academics and students find and organize citations for their research papers. Users can search for research papers on arXiv, upload their own documents, and automatically generate recommended citations for each paragraph, complete with relevance scores. The system streamlines the citation process and ensures users have accurate references for their work.

## Installation
1. Clone repo
```sh
git clone https://github.com/Mantater/Scholar-Athen
cd scholar-athen
```
2. Install dependencies (inside yoda_app folder only)
```sh
cd https://github.com/Mantater/Scholar-Athen/Main_webUI
pip install -r requirements.txt
```
3. Set up environment variables
- Create a `.env` file in the root directory
- Add your API keys, e.g.,
```sh
OR_RPA_KEY=your_openrouter_api_key
```
5. Run Django migrations
```sh
python manage.py makemigrations
python manage.py migrate
```
6. Start the development server:
```sh
python manage.py runserver
```

## Usage
- Search for papers: Enter keywords in the search bar to fetch research papers from arXiv. Results include paper title, authors, publication date, DOI, summary, and PDF link.
- Upload your document: Upload PDF or DOCX files to extract paragraphs and generate recommended citations.
- View citations: Each paragraph displays the top 3 recommended citations with relevance percentages.
- Export citations: Download citations in CSV, JSON, BibTeX, or PDF formats. Citation style can be customized in settings.

## Features
- Search and fetch research papers from arXiv.
- Results ranked by publication date and relevance.
- Upload PDF/DOCX documents and extract text automatically.
- Clean and preprocess text using spaCy.
- Generate keywords and paragraph summaries via LLM.
- Query arXiv API for relevant papers using extracted keywords and summaries.
- Rank results using semantic similarity (SBERT).
- Map top 3 recommended citations to each paragraph with relevance scores.
- Export citations in multiple formats (CSV, JSON, BibTeX, PDF).
- Configure default citation style and export type in user settings.

## License
This project is licensed under the MIT License. See `LICENSE` for details.

## Notes
- The suggested citations are recommendations; please verify for accuracy before using.
- The LLM used is NVIDIA Nemotron Nano 9B V2, accessed via OpenRouter.
- LLM API usage may be rate-limited. Errors related to API limits may appear when generating citations.
- PDF/DOCX upload processing may take a few seconds depending on document length.
- Current Main_webUI is ver10 from archive