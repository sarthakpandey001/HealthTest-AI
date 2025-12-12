import hashlib
import re
import time
import glob
import os, shutil
from typing import Tuple, List, Dict
from google.cloud import firestore, storage
from selenium import webdriver
from selenium_stealth import stealth
# Assuming only_pdf_url_scraper.py is available in the environment
from google.cloud.storage import Client
import vertexai
from vertexai import rag
from pathlib import Path
from git import Repo

from vertexai.rag import RagEmbeddingModelConfig, RagVectorDbConfig, TransformationConfig, ChunkingConfig
from google import genai
import json
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin, urlparse
from google import genai
from google.genai.errors import APIError
from google.genai.types import GenerateContentConfig
from pydantic import BaseModel, Field
from dotenv import load_dotenv,find_dotenv

load_dotenv(dotenv_path=find_dotenv())


# --- GLOBAL CONFIGURATION ---
PROJECT_ID = os.getenv("PROJECT_ID")
PROJECT_LOCATION = os.getenv("PROJECT_LOCATION")
FIRESTORE_COLLECTION = os.getenv("FIRESTORE_COLLECTION")
VAI_REGION = os.getenv("VAI_REGION")
BUCKET_NAME = os.getenv("BUCKET_NAME")
MASTER_RAG_CORPUS = os.getenv("MASTER_RAG_CORPUS")      

# --- SELENIUM SETUP (Global Driver for Scraping/Download) ---
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
# Ensure the temporary download path is absolute and created
pdf_temp_save_path = os.path.join(os.path.abspath('.'), "temp/")
os.makedirs(pdf_temp_save_path, exist_ok=True)
options.add_experimental_option('prefs', {
    "download.default_directory": pdf_temp_save_path,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True
})
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
driver = webdriver.Chrome(options=options)
stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
)

# --- CLIENT INITIALIZATION ---
db = firestore.Client(project=PROJECT_ID)
storage_client = storage.Client()
vertexai.init(project=PROJECT_ID, location=VAI_REGION)
client = genai.Client(vertexai=True, project=PROJECT_ID, location=PROJECT_LOCATION)
top_k_chunks = 15  # Specify how many of the most relevant chunks to retrieve
rag_retrieval_config = rag.RagRetrievalConfig(
    top_k=top_k_chunks,
    # Optional: you can add a filter here if needed, e.g., for vector distance threshold
    # filter=rag.utils.resources.Filter(vector_distance_threshold=0.5),
)
rag_corpora = rag.get_corpus(name=MASTER_RAG_CORPUS)

def repo_to_txt(repo_link):
    global pdf_temp_save_path
    temp_dir = pdf_temp_save_path
    repo_dir = os.path.join(temp_dir, "temp_repo")
    Repo.clone_from(repo_link, repo_dir)
    SOURCE_EXTENSIONS = ['.py', '.js', '.ts', '.html', '.css', '.c', '.cpp', '.java', '.go', '.rs', '.swift', '.rb', '.php', '.md']
    EXCLUDE_DIRS = ['.git', '__pycache__', 'node_modules', '.idea', '.vscode', 'venv', 'env', '.env', 'site-packages']
    clone_path = Path(repo_dir)
    output_file = os.path.join(temp_dir, "source_code.txt")
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for root, dirs, files in os.walk(clone_path, topdown=True):
            new_dirs = []
            for d in dirs:
                include = False
                for ed in EXCLUDE_DIRS: 
                    if ed in d: 
                        include = False
                        break
                if include: new_dirs += d
            dirs[:] = new_dirs
            for file_name in files:
                file_path = Path(root) / file_name
                if file_path.suffix.lower() in SOURCE_EXTENSIONS:
                    try:
                        relative_path = file_path.relative_to(clone_path)
                        outfile.write(f"--- START FILE: {relative_path} ---\n")
                        content = file_path.read_text(encoding='utf-8')
                        outfile.write(content.strip() + '\n') # .strip() cleans up extra leading/trailing whitespace
                        outfile.write(f"--- END FILE: {relative_path} ---\n\n")
                        # print(f"  - Included: {relative_path}")
                    except Exception as e:
                        print(f"  - Skipped (Error {e.__class__.__name__}): {file_path}")
    # print(f"\nAggregation complete. The RAG source file is: **{output_file}**")
    return output_file

def create_source_code_embdeeings(repo_link):
    repo_name = repo_link.split('/')[-1]
    doc_id = hashlib.sha256(repo_link.encode('utf-8')).hexdigest()
    doc_ref = db.collection(FIRESTORE_COLLECTION).document(doc_id)
    print(f"--- STARTING ASYNC CREATION for source code {repo_link} ---")
    
    try:
        # 1. Determine content type and find PDF links
        output_file = repo_to_txt(repo_link)

        rag_file_ids = []
        rag_file_response = rag.upload_file(
            corpus_name=MASTER_RAG_CORPUS,
            path=output_file,
            display_name=repo_name, # Use the filename as the display name
            description="Uploaded via Python SDK example."
        )
        rag_file_ids.append(rag_file_response.name)

        delete_folder_content(pdf_temp_save_path) 
        
        # 3. Update DB with collected information
        doc_ref.update({
            "rag_file_ids": rag_file_ids,
            "processing": False,
            "embeddings_available": True if len(rag_file_ids) else False
        })
        
        print(f"--- ASYNC CREATION COMPLETE for {repo_link}  ---")
        
    except Exception as e:
        print(f"Fatal error during async creation of {repo_link}: {e}")
        doc_ref.update({
            "processing": False,
            "embeddings_available": False,
            "error": str(e)
        })

def delete_source_code_embeddings(repo_link):

    doc_id = hashlib.sha256(repo_link.encode('utf-8')).hexdigest()
    doc_ref = db.collection(FIRESTORE_COLLECTION).document(doc_id)
    initial_data = doc_ref.get().to_dict()
    
    try:
        # 1. Delete GCS files
        # delete_directory_gcs(corpus_name)
        rag_file_ids = initial_data.get("rag_file_ids")

        if rag_file_ids:
            print(f"Deleting {len(rag_file_ids)} RAG Files from the master corpus...")
            for file_id in rag_file_ids:
                try:
                    # Deletes the file resource from the single master corpus
                    rag.delete_file(file_id) 
                    print(f"Deleted RAG File: {file_id}")
                except Exception as e:
                    # Log but continue to ensure GCS/Firestore are cleaned up
                    print(f"Warning: Could not delete RAG File {file_id}. Error: {e}")
        else:
            print(f"No RAG file IDs found to delete for source {repo_link}.")           
        
        doc_ref.delete()
        print(f'Firestore record for {repo_link} deleted.')
        return True
    except Exception as e:
        print(f"Error during synchronous deletion of {repo_link}: {e}")
        return False

def get_enhancement_prompt(software_requirement: str) -> str:
    """
    Drafts a robust prompt to guide the LLM in transforming a software
    requirement into a high-recall regulatory search query.
    """
    return f"""
You are an expert Regulatory Compliance Analyst for medical devices and software (MedTech).
Your task is to analyze a **Software Requirement** and transform it into a **list of specific, technical search queries** 
suitable for retrieving relevant regulatory text chunks from a corpus containing documents like HIPAA, GDPR, ISO 13485, FDA guidance, 
and IEC 62304.

**The output MUST ONLY be the list of generated search queries, separated by semicolons (;). DO NOT include any other text, explanations, 
or conversational filler.**

Focus your queries on finding:
1.  **Specific Regulations/Articles:** Mentioning precise article numbers (e.g., "GDPR Article 17 right to erasure").
2.  **Key Compliance Concepts:** Using exact regulatory terminology (e.g., "data retention period," "audit trail requirements," 
"risk classification," "de-identification method").
3.  **Relevant Standards/Documents:** Explicitly naming the standard when applicable (e.g., "ISO 13485 design change control," 
"IEC 62304 software safety classification").

**SOFTWARE REQUIREMENT TO ANALYZE:**
---
{software_requirement}
---

**GENERATED SEARCH QUERIES (Semicolon separated list ONLY):**
"""

def retrieve_regulations(software_requirement: str):
    """
    Executes the full flow: Enhancement -> Search -> Retrieval.
    """
    # 1. Enhance the query using the LLM
    print(f"-> Enhancing requirement: '{software_requirement[:50]}...'")

    prompt = get_enhancement_prompt(software_requirement)
    
    enhanced_query = ""
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt],
        )
        enhanced_query = response.text

    except Exception as e:
        print(f"An error occurred during query enhancement: {e}")
        return [software_requirement] # Fallback to original query

    
    # 2. Query the RAG corpus with the enhanced queries
    rag_query = software_requirement + "\n" + enhanced_query

    print(f"Query: {rag_query}\n")

    response = rag.retrieval_query(
        rag_resources=[
            rag.RagResource(
                rag_corpus=rag_corpora.name,
                # Optional: you can  specific files within the corpus
                # rag_file_ids=["rag-file-1", "rag-file-2"],
            )
        ],
        text=rag_query,
        rag_retrieval_config=rag_retrieval_config,
    )
    ret_list = []
    for ctx in response.contexts.contexts:
        ret_list.append({
            "text": ctx.text,
            "score": ctx.score,
            "source_uri": ctx.source_uri
        })

    return ret_list

# --- UTILITY FUNCTIONS ---
def fetch_webpage_selenium(url, PROCESSED_URLS):
    if url in PROCESSED_URLS:
        print(f"-> Skipping already processed URL: {url}")
        return None
    PROCESSED_URLS.add(url)
    
    driver.get(url)
    time.sleep(1)
    return driver.page_source

def extract_hyperlinks(soup: BeautifulSoup, BASE_URL) -> List[Dict[str, str]]:
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

class RegulatoryLinkIndices(BaseModel):
    """Schema for the LLM's structured output."""
    indices: list[int] = Field(
        description="A list of 1-based numerical indices corresponding to the structured hyperlinks that are likely regulatory compliance documents, rule books, or governance-related PDFs."
    )

def find_regulatory_links_structured(url: str):
    global client
    """
    1. Prepares the webpage context for the LLM.
    2. Uses the LLM with structured output enforcement to identify link indices.
    3. Programmatically verifies the identified links are actually PDFs.
    """
    print(f"--- Analyzing URL: {url} (Structured Output) ---")
    parsed_url = urlparse(url)
    BASE_URL = f"{parsed_url.scheme}://{parsed_url.netloc}"
    PROCESSED_URLS = set()
    # 1. Fetch, clean, and structure the page data
    # (Assuming these functions are available and work as intended)
    html_content = fetch_webpage_selenium(url, PROCESSED_URLS)
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, 'lxml')
    all_structured_links = extract_hyperlinks(soup, BASE_URL)
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

def delete_folder_content(folder: str):
    """Deletes all files and subdirectories within a given folder."""
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

def delete_directory_gcs(directory_prefix: str):
    """Deletes all objects (files) within a given GCS directory prefix."""
    try:
        bucket = storage_client.bucket(BUCKET_NAME)
    except Exception as e:
        print(f"Error accessing bucket '{BUCKET_NAME}': {e}")
        return

    if not directory_prefix.endswith("/"):
        directory_prefix += "/"
        
    blobs = storage_client.list_blobs(BUCKET_NAME, prefix=directory_prefix)
    blob_names_to_delete = [blob.name for blob in blobs]
    
    if blob_names_to_delete:
        # Note: This operation might fail if the user doesn't have storage:object.delete permission
        try:
            bucket.delete_blobs(blob_names_to_delete)
            print(f"Deleted {len(blob_names_to_delete)} objects in gs://{BUCKET_NAME}/{directory_prefix}")
        except Exception as e:
            print(f"Failed to delete blobs in GCS: {e}")
    else:
        print(f"No objects found with prefix gs://{BUCKET_NAME}/{directory_prefix}. Nothing to delete.")

def check_pdf(url: str) -> bool:
    """Checks if a URL triggers a PDF download using Selenium."""
    if not driver: return False # Safety check if driver failed init
    if url.lower().endswith(('.html', '.htm', '.php', '.aspx')): return False
    
    initial_files = set(os.listdir(pdf_temp_save_path))
    try:
        driver.get(url)
        # Give some time for the potential download to start
        time.sleep(3) 
    except Exception as e:
        print(f"Error accessing URL via Selenium: {e}")
        return False
        
    current_files = set(os.listdir(pdf_temp_save_path))
    new_files = current_files - initial_files
    
    return True if new_files else False


def get_corpus_id_by_display_name(display_name: str) -> str:
    """Finds a Vertex AI RAG Corpus ID given its display name."""
    try:
        corpora_pager = rag.list_corpora()
        for corpus in corpora_pager:
            if corpus.display_name == display_name:
                # Extract the corpus ID (the last segment of the resource name)
                full_name = corpus.name
                match = re.search(r'ragCorpora/(\d+)', full_name)
                return match.group(1) if match else full_name.split('/')[-1]
        return ""
    except Exception as e:
        print(f"An error occurred while listing corpora: {e}")
        return ""

def upload_parent_directory(parent_dir: str, gcs_destination_folder: str = "") -> Tuple[List[str], List[str]]:
    """Uploads content of a local directory to GCS and computes checksums."""
    if not os.path.isdir(parent_dir):
        print(f"Error: Directory '{parent_dir}' does not exist.")
        return [], []

    try:
        bucket = storage_client.bucket(BUCKET_NAME)
    except Exception as e:
        print(f"Error accessing bucket '{BUCKET_NAME}': {e}")
        return [], []

    if gcs_destination_folder and not gcs_destination_folder.endswith('/'):
        gcs_destination_folder += '/'

    gcs_uris = []
    checksums = []
    
    for root, _, files in os.walk(parent_dir):
        for filename in files:
            local_file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(local_file_path, parent_dir)
            
            # Compute MD5 checksum
            with open(local_file_path, 'rb') as f:
                md5_cs = hashlib.md5(f.read()).hexdigest()
            checksums.append(md5_cs)
            
            destination_blob_name = gcs_destination_folder + relative_path.replace(os.path.sep, "/")
            
            print(f"  -> Uploading '{relative_path}' to '{destination_blob_name}'...")
            
            try:
                blob = bucket.blob(destination_blob_name)
                blob.upload_from_filename(local_file_path)
                gcs_uris.append(f'gs://{BUCKET_NAME}/{destination_blob_name}')
            except Exception as e:
                print(f"Error uploading file {local_file_path}: {e}")

    # Delete local temporary files after successful upload
    delete_folder_content(parent_dir)
    print(f"Synchronous upload complete. {len(gcs_uris)} files uploaded and local 'temp/' cleaned.")
    return gcs_uris, checksums

def import_files_to_corpus(corpus_name: str, gcs_uris: List[str]):
    print(f"importing to RAG Corpus: {corpus_name}")
    import_operation = rag.import_files(
        corpus_name=MASTER_RAG_CORPUS,
        paths=gcs_uris,
        transformation_config=TransformationConfig(
            chunking_config=ChunkingConfig(chunk_size=1024, chunk_overlap=200)
        ),
    )
        
    rag_file_resource_names = [file.name for file in import_operation.imported_rag_files]
    return rag_file_resource_names

def create_corpus_async_task(corpus_name: str, link: str):
    """
    The long-running task to scrape, download, upload, and create RAG corpus.
    This runs in a background thread.
    """
    doc_ref = db.collection(FIRESTORE_COLLECTION).document(corpus_name)
    print(f"--- STARTING ASYNC CREATION for {corpus_name} ---")
    
    try:
        # 1. Determine content type and find PDF links
        is_pdf = check_pdf(link)
        doc_type = 'pdf' if is_pdf else 'webpage'
        
        pdf_links_to_download = [link] if is_pdf else find_regulatory_links_structured(link)
        
        # We need to re-run check_pdf on the initial link for non-PDFs 
        # to trigger the download of the link's content into the 'temp/' folder
        if not is_pdf:
            print(f"Scraping links from webpage: {link}")
            # Note: find_regulatory_links_structured already uses Selenium and downloads 
            # the found PDFs to 'temp/'. We just need the list of links.
            pass
            
        # 2. Upload downloaded PDFs (which are now in 'temp/') to GCS and get checksums
        # gcs_uris, checksums = upload_parent_directory(pdf_temp_save_path, corpus_name)
        rag_file_ids = []
        checksums = []
        for pth in glob.glob(os.path.join(pdf_temp_save_path, "*.pdf")):
            with open(pth, 'rb') as f:
                md5_cs = hashlib.md5(f.read()).hexdigest()
            checksums.append(md5_cs)
            print(f"Uploading {pth} to corpus")
            rag_file_response = rag.upload_file(
                corpus_name=MASTER_RAG_CORPUS,
                path=pth,
                display_name=corpus_name, # Use the filename as the display name
                description="Uploaded via Python SDK example."
            )
            rag_file_ids.append(rag_file_response.name)
        delete_folder_content(pdf_temp_save_path) 
        
        # 3. Update DB with collected information
        doc_ref.update({
            "type": doc_type,
            "pdf_links": pdf_links_to_download,
            "rag_file_ids": rag_file_ids,
            "md5_checksums": checksums,
            "processing": False,
            "rag_file_ids": rag_file_ids,
            "embeddings_available": True if len(rag_file_ids) else False
        })
        
        print(f"--- ASYNC CREATION COMPLETE for {corpus_name}  ---")
        
    except Exception as e:
        print(f"Fatal error during async creation of {corpus_name}: {e}")
        doc_ref.update({
            "processing": False,
            "embeddings_available": False,
            "error": str(e)
        })

def update_corpus_async_task(corpus_name: str, link: str):
    """
    The long-running task to re-scrape, check for updates, and re-create RAG corpus.
    This runs in a background thread.
    """
    doc_ref = db.collection(FIRESTORE_COLLECTION).document(corpus_name)
    print(f"--- STARTING ASYNC UPDATE for {corpus_name} ---")

    try:
        # 1. Re-check/re-scrape content (downloads new PDFs to 'temp/')
        initial_data = doc_ref.get().to_dict()
        if not initial_data:
            print(f"Error: Corpus {corpus_name} not found for update.")
            return

        doc_ref.update({"processing": True, "embeddings_available": False})
        
        pdf_links_to_download = []
        # Execute scraping/download logic based on type
        if initial_data.get('type') == 'pdf':
            # For direct PDF links, just check for re-download to 'temp/'
            check_pdf(link)
            pdf_links_to_download = [link]
        else:
            # For web pages, re-scrape for new links (downloads to 'temp/')
            pdf_links_to_download = find_regulatory_links_structured(link)
            
        # 2. Check if files in 'temp/' are actually new
        pdfs_paths = glob.glob(os.path.join(pdf_temp_save_path, '*.pdf'))
        new_checksums_set = set()
        for pth in pdfs_paths:
            with open(pth, 'rb') as f:
                new_checksums_set.add(hashlib.md5(f.read()).hexdigest())

        existing_checksums_set = set(initial_data.get('md5_checksums', []))

        if not new_checksums_set.issubset(existing_checksums_set):
            print("Checksum mismatch detected or new files found. Proceeding with update.")
            
            # 3. Clean up old resources
            # delete_directory_gcs(corpus_name)    
    
            # 4. Upload new content, get new URIs and checksums
            # new_gcs_uris, final_checksums = upload_parent_directory(pdf_temp_save_path, corpus_name)
            rag_file_ids = initial_data.get("rag_file_ids")

            if rag_file_ids:
                print(f"Deleting {len(rag_file_ids)} RAG Files from the master corpus...")
                for file_id in rag_file_ids:
                    try:
                        # Deletes the file resource from the single master corpus
                        rag.delete_file(file_id) 
                        print(f"Deleted RAG File: {file_id}")
                    except Exception as e:
                        # Log but continue to ensure GCS/Firestore are cleaned up
                        print(f"Warning: Could not delete RAG File {file_id}. Error: {e}")
            else:
                print(f"No RAG file IDs found to delete for source {corpus_name}.")           
                # 5. Create new RAG Corpus and import
                #
            rag_file_ids = []
            checksums = []
            for pth in glob.glob(os.path.join(pdf_temp_save_path, "*.pdf")):
                with open(pth, 'rb') as f:
                    md5_cs = hashlib.md5(f.read()).hexdigest()
                checksums.append(md5_cs)
                print(f"Uploading {pth} to corpus")
                rag_file_response = rag.upload_file(
                    corpus_name=MASTER_RAG_CORPUS,
                    path=pth,
                    display_name=corpus_name, # Use the filename as the display name
                    description="Uploaded via Python SDK example."
                )
                rag_file_ids.append(rag_file_response.name)
            delete_folder_content(pdf_temp_save_path) 
        
        # 3. Update DB with collected information
            doc_ref.update({
                "pdf_links": pdf_links_to_download,
                "rag_file_ids": rag_file_ids,
                "md5_checksums": checksums,
                "processing": False,
                "rag_file_ids": rag_file_ids,
                "embeddings_available": True if len(rag_file_ids) else False
            })
    
            # 6. Final DB update
            final_data = {
                "processing": False,
                "embeddings_available": True,
                "md5_checksums": list(new_checksums_set),
            }
            doc_ref.update(final_data)
            print(f"--- ASYNC UPDATE COMPLETE for {corpus_name} ---")

        else:
            print('Checksum match or no new content. No update required.')
            delete_folder_content(pdf_temp_save_path)
            doc_ref.update({"processing": False, "embeddings_available": True})
            print(f"--- ASYNC UPDATE SKIPPED for {corpus_name} ---")

    except Exception as e:
        print(f"Fatal error during async update of {corpus_name}: {e}")
        doc_ref.update({
            "processing": False,
            "embeddings_available": False,
            "error": str(e)
        })

# --- SYNCHRONOUS TASK (Fast enough for API) ---

def delete_corpus_sync_task(corpus_name: str) -> bool:
    """Deletes all associated resources synchronously."""
    doc_ref = db.collection(FIRESTORE_COLLECTION).document(corpus_name)
    initial_data = doc_ref.get().to_dict()
    
    try:
        # 1. Delete GCS files
        # delete_directory_gcs(corpus_name)
        rag_file_ids = initial_data.get("rag_file_ids")

        if rag_file_ids:
            print(f"Deleting {len(rag_file_ids)} RAG Files from the master corpus...")
            for file_id in rag_file_ids:
                try:
                    # Deletes the file resource from the single master corpus
                    rag.delete_file(file_id) 
                    print(f"Deleted RAG File: {file_id}")
                except Exception as e:
                    # Log but continue to ensure GCS/Firestore are cleaned up
                    print(f"Warning: Could not delete RAG File {file_id}. Error: {e}")
        else:
            print(f"No RAG file IDs found to delete for source {corpus_name}.")           
        
        doc_ref.delete()
        print(f'Firestore record for {corpus_name} deleted.')
        return True
    except Exception as e:
        print(f"Error during synchronous deletion of {corpus_name}: {e}")
        return False

