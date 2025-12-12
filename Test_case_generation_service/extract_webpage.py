
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def fetch_webpage_playwright(url: str, timeout: int = 15) -> Optional[str]:
    """
    Fetches HTML content by executing JavaScript and waiting for the 
    'networkidle' state using Playwright.
    """
    from playwright.sync_api import sync_playwright
    from time import sleep

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            
            # 💡 The direct equivalent of 'Wait For Load State networkidle'
            page.goto(
                url, 
                wait_until="networkidle", # Waits until no more than 0 network connections 
                                          # have been active during the last 500 milliseconds.
                timeout=timeout * 1000 # Playwright uses milliseconds
            )
            
            # sleep(60)
            html_content = page.content() # Get the fully rendered HTML/DOM
            browser.close()
            
            print(f"-> Successfully fetched (Playwright/networkidle): {url}")
            return html_content
    except Exception as e:
        print(f"Error ({url}): An error occurred during dynamic fetch - {e}")
        return None


def fetch_webpage(url: str) -> Optional[str]:
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        return response.text
    except requests.exceptions.HTTPError as e:
        print(f"Error: HTTP error occurred - {e}")
    except requests.exceptions.ConnectionError as e:
        print(f"Error: Could not connect to the URL - {e}")
    except requests.exceptions.Timeout:
        print("Error: The request timed out.")
    except requests.exceptions.RequestException as e:
        print(f"Error: An unexpected error occurred during the request - {e}")
    return None

def extract_hyperlinks(soup: BeautifulSoup) -> List[Dict[str, str]]:
    hyperlinks = []
    for link in soup.find_all('a', href=True):
        text = link.get_text(strip=True)
        href = link['href']
        if text and href.strip():
            hyperlinks.append({
                'text': text,
                'href': href
            })
    return hyperlinks

def create_llm_context_string(page_text: str, structured_links: List[Dict[str, str]]) -> str:
    context_string = f"--- MAIN WEBPAGE CONTENT ---\n\n{page_text}\n\n"
    context_string += "========================================================================\n"
    context_string += "--- STRUCTURED HYPERLINK DATA ---\n"
    context_string += "========================================================================\n"

    if not structured_links:
        context_string += "No hyperlinks were found.\n"
        return context_string

    formatted_links = []
    for i, item in enumerate(structured_links):
        link_line = (
            f"[{i+1}]: Anchor Text: '{item['text']}' | URL: '{item['href']}'"
        )
        formatted_links.append(link_line)

    context_string += "\n".join(formatted_links)
    return context_string

def prepare_for_llm(url: str) -> str:
    # html_content = fetch_webpage(url)
    html_content = fetch_webpage_playwright(url)
    if not html_content:
        return "Failed to fetch webpage content."
    soup = BeautifulSoup(html_content, 'lxml') 
    structured_links = extract_hyperlinks(soup)
    for element in soup(["script", "style", "header", "footer", "nav"]):
        element.decompose()
    page_text = soup.get_text(separator='\n', strip=True)
    # max_chars = 5000
    # if len(page_text) > max_chars:
    #     print(f"-> Warning: Page text truncated from {len(page_text)} to {max_chars} characters.")
    #     page_text = page_text[:max_chars] + "\n... [Content Truncated] ..."
    llm_context_string = create_llm_context_string(page_text, structured_links)
    return llm_context_string

if __name__ == '__main__':
    # example_url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
    example_url = "https://www.meity.gov.in/documents/act-and-policies?page=1"
    final_llm_input_string = prepare_for_llm(example_url)

    print("\n" + "="*80)
    print("--- FINAL SINGLE CONTEXT STRING FOR LLM ---")
    print("="*80)
    print(final_llm_input_string)
    print("="*80)

