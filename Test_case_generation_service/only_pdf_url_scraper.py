import os
from flask.app import cli
import requests
import json
import time
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin, urlparse
from google import genai
from google.genai.errors import APIError
from google.genai.types import GenerateContentConfig
from pydantic import BaseModel, Field
from enum import Enum
from selenium import webdriver
from selenium_stealth import stealth

# --- SELENIUM SETUP ---
options = webdriver.ChromeOptions()
# options.add_argument("--headless")
pdf_temp_save_path = os.path.join(os.path.abspath('.'),"temp/")
os.makedirs(pdf_temp_save_path, exist_ok=True)
options.add_experimental_option('prefs', {
    "download.default_directory": pdf_temp_save_path, #Change default directory for downloads
    "download.prompt_for_download": False, #To auto download the file
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True #It will not show PDF directly in chrome
})
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
driver = webdriver.Chrome(options=options)
import json

PROJECT_ID = "gen-ai-hackathon-476616"
PROJECT_LOCATION = "global"
client = genai.Client(vertexai=True, project=PROJECT_ID, location=PROJECT_LOCATION)

class RegulatoryLinkIndices(BaseModel):
    """Schema for the LLM's structured output."""
    indices: list[int] = Field(
        description="A list of 1-based numerical indices corresponding to the structured hyperlinks that are likely regulatory compliance documents, rule books, or governance-related PDFs."
    )

stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        )


# --- GLOBAL CONFIGURATION AND STORAGE ---
MAX_DEPTH = 2  # Stop after 2 levels of link traversal
PDF_LINKS: Set[str] = set() # Store unique URLs for documents
PROCESSED_URLS: Set[str] = set() # Keep track of visited URLs
BASE_URL = "" # Will be set by the initial call

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def check_pdf(url):
    if url[-5:]=='.html': return False
    initial_files = set(os.listdir(pdf_temp_save_path))
    driver.get(url)
    time.sleep(1)
    current_files = set(os.listdir(pdf_temp_save_path))
    new_files = current_files - initial_files
    return True if new_files else False

def fetch_webpage_selenium(url):
    if url in PROCESSED_URLS:
        print(f"-> Skipping already processed URL: {url}")
        return None
    PROCESSED_URLS.add(url)
    
    driver.get(url)
    time.sleep(1)
    return driver.page_source

def extract_hyperlinks(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """Extracts anchor text and converts hrefs to absolute URLs."""
    hyperlinks = []
    for link in soup.find_all('a', href=True):
        text = link.get_text(strip=True)
        href = urljoin(BASE_URL, link['href'])
        
        hyperlinks.append({
            'text': text,
            'href': href
        })
    return hyperlinks

def prepare_for_llm(url: str) -> Optional[tuple[str, str]]:
    """Fetches, cleans, and formats page data."""
    html_content = fetch_webpage_selenium(url)
    if not html_content:
        return None
    
    soup = BeautifulSoup(html_content, 'lxml') 
    structured_links = extract_hyperlinks(soup)
    
    for element in soup(["script", "style", "header", "footer", "nav", "aside"]):
        element.decompose()
        
    page_text = soup.get_text(separator='\n', strip=True)
    
    llm_context_string = _create_llm_context_string(page_text, structured_links)
    
    return llm_context_string, page_text

def _create_llm_context_string(page_text: str, structured_links: List[Dict[str, str]]) -> str:
    """Helper function to format context string."""
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

def find_regulatory_links_structured(url: str):
    global client
    """
    1. Prepares the webpage context for the LLM.
    2. Uses the LLM with structured output enforcement to identify link indices.
    3. Programmatically verifies the identified links are actually PDFs.
    """
    print(f"--- Analyzing URL: {url} (Structured Output) ---")
    global BASE_URL
    parsed_url = urlparse(url)
    BASE_URL = f"{parsed_url.scheme}://{parsed_url.netloc}"
    # 1. Fetch, clean, and structure the page data
    # (Assuming these functions are available and work as intended)
    html_content = fetch_webpage_selenium(url)
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, 'lxml')
    all_structured_links = extract_hyperlinks(soup)
    llm_context_string = _create_llm_context_string(soup.get_text(separator='\n', strip=True), all_structured_links)
    
    if not all_structured_links:
        print("No hyperlinks found to analyze.")
        return []

    # 2. Define the LLM prompt and enforce structured output
    
    # The prompt can be simpler now, as the schema dictates the format.
    prompt = f"""
    Analyze the following webpage content and the structured hyperlink data.
    
    **Goal:** Identify which of the structured hyperlinks are *most likely* to point to a PDF for **regulatory compliance document**, **rule book**, or other **formal/official document related to regulations**.
    
    Return the 1-based numerical indices of the most relevant links.

    --- CONTEXT TO ANALYZE ---
    {llm_context_string}
    """

    # --- ENFORCING STRUCTURED OUTPUT ---
    generation_config = {
        "response_mime_type": "application/json",
        "response_schema": RegulatoryLinkIndices,
    }
    # ------------------------------------

    print("-> Sending context to LLM for structured link identification...")
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt],
            config=generation_config # Pass the configuration here
        )
    
        # 3. LLM Output Parsing is now guaranteed to be JSON according to the schema
        
        # Load the JSON string from response.text
        response_data = json.loads(response.text)
        
        # Access the list of indices using the defined field name 'indices'
        llm_link_indices = response_data.get('indices', [])
        print(f"-> LLM suggested indices: {llm_link_indices}")

        potential_links = []
        for index in llm_link_indices:
            try:
                # Convert the 1-based index from the LLM to a 0-based list index
                link_data = all_structured_links[index - 1] 
                link_href = link_data['href']
                
                # --- APPLY ABSOLUTE URL LOGIC HERE ---
                # Check if the URL is missing a scheme (i.e., it looks like a path or relative URL)
                if not urlparse(link_href).scheme:
                    # Use urljoin with BASE_URL to make it fully absolute
                    absolute_link = urljoin(BASE_URL, link_href)
                    potential_links.append(absolute_link)
                    # print(f"   (Fixed Relative URL: {link_href} -> {absolute_link})")
                else:
                    # It's already absolute (or urljoin already made it absolute from extraction)
                    potential_links.append(link_href)

            except IndexError:
                print(f"Warning: LLM returned invalid index {index}. Skipping.")
        
        potential_links = list(set(potential_links))
        print(f"-> Potential links after absoluting: {potential_links}")
        # 4. Final Verification: Check if the links are actually PDFs
        final_pdf_links = []
        for link in potential_links:
            # Assumes get_content_type(url) is available
            if check_pdf(link):
                final_pdf_links.append(link)
                # print(f"   **MATCH FOUND (PDF): {link}**") # Uncomment for verbose logging
        
        return final_pdf_links

    except Exception as e:
        print(f"An error occurred during LLM generation or parsing: {e}")
        return []

# if __name__ == "__main__":
#     url = "https://www.hhs.gov/hipaa/for-professionals/index.html"
#     url = "https://gdpr-info.eu/"
#     # url = "https://dpdpa.com/"
#     links = find_regulatory_links_structured(client, url)
#     print(links)

