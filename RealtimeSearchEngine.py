# Backend/RealtimeSearchEngine.py
"""
Robust realtime search:
- Wikipedia OpenSearch (with User-Agent)
- Wikipedia page-fallback via BeautifulSoup
- googlesearch (if installed)
- Cohere fallback
- Always returns sanitized string (no exceptions propagate)
"""

import os
import datetime
import traceback
from json import dump, load
from dotenv import dotenv_values

# network tools
import requests
from bs4 import BeautifulSoup

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
env_vars = dotenv_values(os.path.join(PROJECT_ROOT, ".Env"))

COHERE_API_KEY = env_vars.get("COHERE_API_KEY")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")

# chatlog path
chatlog_path = os.path.join(PROJECT_ROOT, "Data", "ChatLog.json")
os.makedirs(os.path.dirname(chatlog_path), exist_ok=True)
if not os.path.exists(chatlog_path):
    with open(chatlog_path, "w", encoding="utf-8") as f:
        dump([], f)

# try import googlesearch if available
try:
    from googlesearch import search as google_search
    _HAS_GOOGLESEARCH = True
except Exception:
    google_search = None
    _HAS_GOOGLESEARCH = False

# try init Cohere client if API key present
co = None
if COHERE_API_KEY:
    try:
        import cohere
        co = cohere.Client(api_key=COHERE_API_KEY)
    except Exception as e:
        print("[RealtimeSearchEngine] Cohere init failed:", e)
        co = None

# helpers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def _sanitize_text(text: str) -> str:
    if not text:
        return ""
    s = text.replace("**", "")     # remove bold markers
    s = s.replace("`", "")         # remove inline code markers
    # normalize whitespace and remove repeated blank lines
    lines = [ln.strip() for ln in s.splitlines()]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines)

def _local_datetime_answer(prompt: str):
    low = prompt.lower()
    if any(k in low for k in ["today's date", "what is today's date", "what is the date", "current date", "date today", "date now"]):
        now = datetime.datetime.now()
        return f"The current date is {now.strftime('%A, %d %B %Y')}."
    if any(k in low for k in ["what time", "current time", "what is the time", "time now", "what's the time"]):
        now = datetime.datetime.now()
        return f"The current time is {now.strftime('%H:%M:%S')}."
    return None

def _wiki_opensearch(query: str, limit: int = 3) -> str:
    """Try the official OpenSearch endpoint with headers. Return formatted results or None."""
    try:
        params = {
            "action": "opensearch",
            "search": query,
            "limit": limit,
            "namespace": 0,
            "format": "json"
        }
        resp = requests.get("https://en.wikipedia.org/w/api.php", params=params, headers=HEADERS, timeout=6)
        if resp.status_code != 200:
            return None
        # attempt JSON parse
        try:
            data = resp.json()
        except Exception:
            # if not JSON, bail (page may be blocked or returned HTML)
            return None
        if not data or len(data) < 4:
            return None
        titles = data[1]
        descs = data[2]
        links = data[3]
        if not titles:
            return None
        pieces = []
        for i, title in enumerate(titles):
            desc = descs[i] if i < len(descs) else ""
            link = links[i] if i < len(links) else ""
            if desc:
                pieces.append(f"{i+1}. {title}: {desc}\n{link}")
            else:
                pieces.append(f"{i+1}. {title}\n{link}")
        return "\n\n".join(pieces)
    except Exception as e:
        print("[RealtimeSearchEngine] _wiki_opensearch error:", e)
        traceback.print_exc()
        return None

def _wiki_page_first_paragraph(query: str) -> str:
    """
    Search Wikipedia via its search page and try to extract the first paragraph
    of the top result using BeautifulSoup.
    """
    try:
        # Use the search endpoint that redirects to the most likely article (special:search)
        params = {"search": query}
        resp = requests.get("https://en.wikipedia.org/w/index.php", params=params, headers=HEADERS, timeout=6)
        if resp.status_code != 200:
            return None
        html = resp.text
        soup = BeautifulSoup(html, "html.parser")
        # If the response is the search results page, find first result link
        # Otherwise, if redirected to an article, extract the first paragraph
        # Find first paragraph in content
        # Article content is under id="mw-content-text"
        content = soup.find(id="mw-content-text")
        if not content:
            return None
        # prefer paragraphs directly under content
        p = content.find("p")
        if p and p.get_text(strip=True):
            title_tag = soup.find(id="firstHeading")
            title = title_tag.get_text(strip=True) if title_tag else query
            text = p.get_text(strip=True)
            # find canonical link
            canonical = None
            link_tag = soup.find("link", {"rel": "canonical"})
            if link_tag and link_tag.get("href"):
                canonical = link_tag["href"]
            if canonical:
                return f"{title}: {text}\n{canonical}"
            else:
                return f"{title}: {text}"
        return None
    except Exception as e:
        print("[RealtimeSearchEngine] _wiki_page_first_paragraph error:", e)
        traceback.print_exc()
        return None

def _google_search_text(query: str, num_results: int = 5) -> str:
    """
    Combined helper: first try Wiki OpenSearch, then page-scrape, then googlesearch.
    Returns string or None.
    """
    # 1) Wikipedia OpenSearch
    wiki = _wiki_opensearch(query, limit=3)
    if wiki:
        return wiki

    # 2) Wikipedia page first paragraph fallback
    wiki2 = _wiki_page_first_paragraph(query)
    if wiki2:
        return wiki2

    # 3) Attempt googlesearch if available
    if _HAS_GOOGLESEARCH and google_search is not None:
        try:
            results = list(google_search(query, num_results=num_results))
            if results:
                pieces = []
                for i, r in enumerate(results, start=1):
                    try:
                        title = getattr(r, "title", None)
                        desc = getattr(r, "description", None)
                        link = getattr(r, "link", None)
                        if not title and isinstance(r, str):
                            pieces.append(f"{i}. {r}")
                        else:
                            parts = []
                            if title:
                                parts.append(title)
                            if desc:
                                parts.append(desc)
                            if link:
                                parts.append(link)
                            pieces.append(f"{i}. " + " - ".join(parts))
                    except Exception:
                        pieces.append(f"{i}. {str(r)}")
                return "\n\n".join(pieces)
        except Exception as e:
            print("[RealtimeSearchEngine] googlesearch attempt error:", e)

    # none found
    return None

def _cohere_answer_via_chat(query: str) -> str:
    """Ask Cohere to answer the query as best it can, with disclaimer. Returns sanitized string."""
    if not co:
        return None
    try:
        system_msg = (
            f"You are an assistant that helps provide factual short answers when possible. "
            f"If the question asks for current-time or live facts, respond that you do not have live browser access but provide the best answer you have and include a short disclaimer."
        )
        prompt = f"{system_msg}\n\nQuestion: {query}\n\nProvide a concise answer, then a short one-paragraph summary if relevant."
        # Try modern chat call
        try:
            resp = co.chat(model="command-a-03-2025", message=prompt, temperature=0.3)
            text = getattr(resp, "text", None) or str(resp)
            return _sanitize_text(text)
        except Exception as e:
            print("[RealtimeSearchEngine] co.chat failed:", e)
            # try generate fallback if present
            try:
                if hasattr(co, "generate"):
                    gen = co.generate(model="command-a-03-2025", prompt=prompt, max_tokens=300)
                    gens = getattr(gen, "generations", None)
                    if gens and len(gens) > 0:
                        text = getattr(gens[0], "text", None) or str(gens[0])
                        return _sanitize_text(text)
            except Exception as e2:
                print("[RealtimeSearchEngine] co.generate fallback failed:", e2)
        return None
    except Exception as e:
        print("[RealtimeSearchEngine] unexpected cohere error:", e)
        traceback.print_exc()
        return None

def RealtimeSearchEngine(prompt: str) -> str:
    """
    Main entry. Given a prompt (assumed flagged as 'realtime ...'), return a string.
    Will not raise exceptions to caller.
    """
    try:
        # 1) local date/time quick answers
        local = _local_datetime_answer(prompt)
        if local:
            return local

        # 2) try web (wiki / google)
        search_text = _google_search_text(prompt, num_results=5)
        if search_text:
            # try to summarize with cohere if possible
            if co:
                try:
                    summary = _cohere_answer_via_chat(f"Summarize the following search results and give a short direct answer:\n\n{search_text}")
                    if summary:
                        return summary
                except Exception as e:
                    print("[RealtimeSearchEngine] summarization error:", e)
                    traceback.print_exc()
            # fallback: return raw search_text sanitized
            return _sanitize_text(search_text)

        # 3) if search not available, try direct Cohere answer (best-effort)
        co_ans = _cohere_answer_via_chat(prompt)
        if co_ans:
            return co_ans

        # 4) final fallback message
        return "Sorry — I can't fetch live web results right now. Please check a reliable web source (news site or official page)."
    except Exception as e:
        print("[RealtimeSearchEngine] unexpected error:", e)
        traceback.print_exc()
        return "Sorry, something went wrong while fetching realtime information."
