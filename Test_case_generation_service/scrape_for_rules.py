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
import time

options = webdriver.ChromeOptions()
# options.add_argument("start-maximized")

options.add_argument("--headless")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
driver = webdriver.Chrome(options=options)# , executable_path=r"C:\Users\DIPRAJ\Programming\adclick_bot\chromedriver.exe")

stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        )

PROJECT_ID = "gen-ai-hackathon-476616"
PROJECT_LOCATION = "global"
# --- GLOBAL CONFIGURATION AND STORAGE ---
MAX_DEPTH = 3 # Stop after 3 levels of link traversal
FINAL_RULE_TEXT: List[str] = []
PDF_LINKS: Set[str] = set() # Store unique URLs for documents
PROCESSED_URLS: Set[str] = set() # Keep track of visited URLs
BASE_URL = "" # Will be set by the initial call

# --- PYDANTIC SCHEMAS FOR STRUCTURED OUTPUT ---

class ShortlistedLinks(BaseModel):
    """Schema for the Link Prioritization step (returns a list of promising URLs)."""
    # Using a simple list structure in the prompt instruction
    # The final output is an array of strings, but we wrap it in a Pydantic class
    # for explicit schema definition, though List[str] is also supported.
    urls: List[str] = Field(description="A list of absolute URLs that are most likely to contain the full regulatory text or lead directly to it (e.g., chapters, articles, PDFs).")

class ClassificationResult(str, Enum):
    """Schema for the Content Classification step (returns one of three fixed words)."""
    YES = "YES"        # Page contains final rule text
    NO = "NO"          # Page is irrelevant or a dead end
    PROCEED = "PROCEED"  # Page is an index/Table of Contents, suggesting further exploration

# --- UTILITY AND FETCH FUNCTIONS (Unchanged logic) ---

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def fetch_webpage_selenium(url):
    if url in PROCESSED_URLS:
        print(f"-> Skipping already processed URL: {url}")
        return None
    PROCESSED_URLS.add(url)

    driver.get(url)
    time.sleep(1)
    return driver.page_source

def fetch_webpage(url: str) -> Optional[str]:
    """Fetches HTML content from a given URL with error handling."""
    if url in PROCESSED_URLS:
        print(f"-> Skipping already processed URL: {url}")
        return None
    PROCESSED_URLS.add(url)
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status() 
        print(f"-> Successfully fetched: {url}")
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error ({url}): An error occurred - {e}")
        return None

def extract_hyperlinks(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """Extracts anchor text and converts hrefs to absolute URLs."""
    hyperlinks = []
    for link in soup.find_all('a', href=True):
        text = link.get_text(strip=True)
        href = urljoin(BASE_URL, link['href'])
        
        # Only include links within the same domain
        if urlparse(href).netloc == urlparse(BASE_URL).netloc and text and href.strip():
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
    
    # Remove boilerplate elements
    for element in soup(["script", "style", "header", "footer", "nav", "aside"]):
        element.decompose()
        
    page_text = soup.get_text(separator='\n', strip=True)
    
    # Truncate content for LLM context, if needed
    # max_chars = 5000 
    # if len(page_text) > max_chars:
    #     page_text = page_text[:max_chars] + "\n... [Content Truncated] ..."

    # Re-use the context string builder for the text + links
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

# --- VERTEX AI / GEMINI CORE LOGIC - USING SCHEMA ---

def get_llm_structured_urls(client: genai.Client, context: str) -> List[str]:
    """
    Uses LLM for link prioritization with a native JSON schema.
    Returns: List of absolute URLs.
    """
    # Prompt is simplified as the schema handles the structure enforcement
    LINK_PRIORITIZATION_PROMPT = """
    Analyze the MAIN WEBPAGE CONTENT and the STRUCTURED HYPERLINK DATA below.
    Your primary goal is to find content relevant to **compliance test case generation for medical software**.

    Identify the absolute URLs that are most likely to contain:
    1.  **Technical Requirements:** (e.g., 'Encryption', 'Access Control', 'Audit Logs', 'API Security').
    2.  **Implementation Protocols:** (e.g., 'Protocol', 'Technical Appendix', 'Implementation Guide', 'Software Specifications').
    3.  **Specific Data Handling Rules:** (e.g., 'Data Retention', 'De-identification', 'Breach Notification Procedures').
    4.  **Specific Regulatory Text:** (e.g., 'Article', 'Section', 'Clause', 'Standard').

    Only return links that appear promising for defining specific, testable requirements for a medical software system.
    """    
    full_prompt = LINK_PRIORITIZATION_PROMPT + "\n\n" + context

    config = GenerateContentConfig(
        # Set the output format to JSON
        response_mime_type="application/json", 
        # Define the structure using the Pydantic model
        response_schema=ShortlistedLinks, 
        temperature=0.0
    )
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=full_prompt,
            config=config
        )
        # The response text is valid JSON, which is automatically parsed 
        # based on the ShortlistedLinks Pydantic model.
        # We parse the text and access the 'urls' field.
        parsed_data = ShortlistedLinks.parse_raw(response.text)
        return parsed_data.urls 
        
    except (APIError, json.JSONDecodeError, Exception) as e:
        print(f"\n[LLM ERROR] Link Selection failed with native schema: {e}. Skipping LLM step.")
        return []

def get_llm_classification(client: genai.Client, page_text: str) -> str:
    """
    Uses LLM to classify content (YES/NO/PROCEED) with native ENUM schema.
    Returns: The string value of the classification.
    """
    CONTENT_CLASSIFICATION_PROMPT = """
    Analyze the page content below. Classify it strictly using the provided categories:
    - **YES**: If the page contains the **actual, final, specific technical or operational rule/requirement** directly applicable to medical software implementation (e.g., 'All patient data must be encrypted using AES-256', 'Access logs shall be retained for 6 years', 'Breach notification must occur within 72 hours').
    - **NO**: If the page is irrelevant (e.g., 'Contact Us', news, high-level policy summaries without specific numbers, or general organizational history).
    - **PROCEED**: If the page is a navigational index, a table of contents, a chapter list, or a high-level overview that **clearly directs you to the detailed technical sections** (e.g., a link labeled 'Technical Implementation Guide' or 'Appendix C: Encryption Standards').
    """    
    full_prompt = CONTENT_CLASSIFICATION_PROMPT + "\n\n" + page_text
    
    config = GenerateContentConfig(
        # Force the model to select one of the ENUM values
        response_mime_type="text/x.enum", 
        # Define the structure using the Enum class
        response_schema=ClassificationResult, 
        temperature=0.0
    )
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=full_prompt,
            config=config
        )
        # The response text will be one of the enum strings ('YES', 'NO', 'PROCEED')
        return response.text.strip().upper()
    except APIError as e:
        print(f"\n[LLM ERROR] Classification failed with native schema: {e}. Defaulting to 'NO'.")
        return "NO"

# --- RECURSIVE TRAVERSAL FUNCTION (Logic remains the same) ---

def recursive_scraper(
    url: str, 
    client: genai.Client, 
    current_depth: int = 0
):
    """The main recursive function for scraping and LLM decision-making."""
    global FINAL_RULE_TEXT, PDF_LINKS

    if current_depth > MAX_DEPTH:
        print(f"-> Max depth reached for: {url}")
        return
    
    if url in PROCESSED_URLS and current_depth > 0:
        return
    
    print(f"\n[{current_depth}/{MAX_DEPTH}] Processing: {url}")

    # 1. Check for PDF/Document link (always prioritize downloading documents)
    if url.lower().endswith(('.pdf', '.doc', '.docx', '.rtf')):
        PDF_LINKS.add(url)
        print(f"-> Found PDF/Document link, saving and stopping path.")
        return

    # 2. Fetch and Prepare Content
    result = prepare_for_llm(url)
    if not result:
        return
    
    llm_context_string, page_text = result

    # 3. LLM Content Classification (Is this the final rule text?)
    classification = get_llm_classification(client, page_text)
    print(f"-> Classification result: {classification}")

    if classification == ClassificationResult.YES.value:
        # Found the goal: save text and stop recursion down this path
        print(f"*** Found final rule text! Saving content from: {url}")
        FINAL_RULE_TEXT.append(f"--- SOURCE URL: {url} ---\n\n{page_text}\n\n")
        return
    
    elif classification == ClassificationResult.NO.value:
        # Irrelevant page: stop recursion down this path
        print("-> Irrelevant page, stopping path.")
        return

    # 4. LLM Link Prioritization (If classification is "PROCEED")
    print("-> Index page found, performing link prioritization...")
    shortlisted_urls = get_llm_structured_urls(client, llm_context_string)
    
    if not shortlisted_urls:
        print("-> LLM returned no promising links or encountered an error. Stopping path.")
        return
    
    # 5. Recursive Call
    print(f"-> Shortlisted {len(shortlisted_urls)} links for next level.")
    # 
    for next_url in shortlisted_urls:
        # A short delay helps prevent overwhelming the target website
        # time.sleep(1) 
        recursive_scraper(next_url, client, current_depth + 1)


# --- MAIN EXECUTION BLOCK ---

def run_scraper(initial_url: str):
    """Initializes client and starts the scraping process."""
    global BASE_URL, FINAL_RULE_TEXT, PDF_LINKS, PROCESSED_URLS
    
    try:
        # Initialize the client.
        client = genai.Client(vertexai=True, project=PROJECT_ID, location=PROJECT_LOCATION)
        print("Vertex AI Client initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize Vertex AI client: {e}")
        return
        
    BASE_URL = initial_url
    
    # Clear previous results and run
    FINAL_RULE_TEXT = []
    PDF_LINKS = set()
    PROCESSED_URLS = set()

    recursive_scraper(initial_url, client)
    
    # 6. Final Output Handling
    print("\n" + "="*80)
    print("                 SCRAPING COMPLETE")
    print("="*80)
    
    # Save Rule Text
    text_filename = "scraped/final_regulatory_rules.txt"
    with open(text_filename, 'w', encoding='utf-8') as f:
        f.write("\n\n" + "-"*40 + " END OF SECTION " + "-"*40 + "\n\n".join(FINAL_RULE_TEXT))
    print(f"✅ Extracted Rule Text saved to: {text_filename} (Total sections: {len(FINAL_RULE_TEXT)})")

    # Save PDF/Link List
    links_filename = "scraped/download_links.txt"
    with open(links_filename, 'w', encoding='utf-8') as f:
        f.write("\n".join(sorted(list(PDF_LINKS))))
    print(f"✅ PDF/Document Links saved to: {links_filename} (Total links: {len(PDF_LINKS)})")

# --- Example Usage ---
# NOTE: Replace with your actual regulatory URL
# INITIAL_TARGET_URL = "https://gdpr-info.eu/"
INITIAL_TARGET_URL = "https://dpdpa.com/dpdparules.html"
run_scraper(INITIAL_TARGET_URL)
driver.quit()
