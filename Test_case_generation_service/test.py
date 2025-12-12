PROJECT_ID = "gen-ai-hackathon-476616"
PROJECT_LOCATION = "global"
FIRESTORE_COLLECTION = "rag_corpuses"
VAI_REGION = "us-east4"
BUCKET_NAME = "regulatory_files"

import hashlib
import re
import time
import glob
import os, shutil
from typing import Tuple
from google.cloud import firestore, storage
from selenium import webdriver
from selenium_stealth import stealth
from only_pdf_url_scraper import find_regulatory_links_structured
from google.cloud.storage import Client, transfer_manager
from pathlib import Path
import vertexai
from vertexai import rag
from vertexai.rag import RagEmbeddingModelConfig, RagVectorDbConfig, TransformationConfig, ChunkingConfig

# --- SELENIUM SETUP ---
# options = webdriver.ChromeOptions()
# options.add_argument("--headless")
# pdf_temp_save_path = os.path.join(os.path.abspath('.'),"temp/")
# os.makedirs(pdf_temp_save_path, exist_ok=True)
# options.add_experimental_option('prefs', {
#     "download.default_directory": pdf_temp_save_path, #Change default directory for downloads
#     "download.prompt_for_download": False, #To auto download the file
#     "download.directory_upgrade": True,
#     "plugins.always_open_pdf_externally": True #It will not show PDF directly in chrome
# })
# options.add_experimental_option("excludeSwitches", ["enable-automation"])
# options.add_experimental_option('useAutomationExtension', False)
# driver = webdriver.Chrome(options=options)
# stealth(driver,
#         languages=["en-US", "en"],
#         vendor="Google Inc.",
#         platform="Win32",
#         webgl_vendor="Intel Inc.",
#         renderer="Intel Iris OpenGL Engine",
#         fix_hairline=True,
# )

def delete_folder_content(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def delete_directory_gcs(directory_prefix):
    """Deletes all objects (files) within a given directory prefix."""

    try:
        bucket = storage_client.bucket(BUCKET_NAME)
    except Exception as e:
        print(f"Error accessing bucket '{BUCKET_NAME}': {e}")
        return []
    if not directory_prefix.endswith("/"):
        directory_prefix += "/"
    blobs = storage_client.list_blobs(
        BUCKET_NAME, prefix=directory_prefix
    )
    blob_names_to_delete = [blob.name for blob in blobs]
    if blob_names_to_delete:
        bucket.delete_blobs(blob_names_to_delete)
        print(f"Deleted {len(blob_names_to_delete)} objects in gs://{BUCKET_NAME}/{directory_prefix}")
    else:
        print(f"No objects found with prefix gs://{BUCKET_NAME}/{directory_prefix}. Nothing to delete.")

def check_pdf(url):
    if url[-5:]=='.html': return False
    initial_files = set(os.listdir(pdf_temp_save_path))
    driver.get(url)
    time.sleep(1)
    current_files = set(os.listdir(pdf_temp_save_path))
    new_files = current_files - initial_files
    return True if new_files else False

db = firestore.Client(project=PROJECT_ID)
storage_client = storage.Client()
vertexai.init(project=PROJECT_ID, location=VAI_REGION)
# doc_ref = db.collection(FIRESTORE_COLLECTION).document('test')
# initial_data = {
#     "name": "corpus_name",
#     "link": "link",
#     "type": "doc_type",
#     "pdf_links": [], # Will be updated after download
#     "embeddings_available": False,
#     "processing": True
# }
# doc_ref.set(initial_data)
#
def get_corpus_id_by_display_name(project_id: str, location: str, display_name: str) -> str:
    """
    Finds a Vertex AI RAG Corpus ID given its display name.
    
    Args:
        project_id: Your Google Cloud project ID.
        location: The region where the corpus is located.
        display_name: The human-readable name of the corpus.

    Returns:
        The Corpus ID (a string of digits) or None if not found.
    """
    try:
        # Use list_corpora() to retrieve all corpora in the location
        # This returns an iterable pager object
        corpora_pager = rag.list_corpora()
        
        # Iterate through all corpora
        for corpus in corpora_pager:
            if corpus.display_name == display_name:
                # The full resource name is in the format: 
                # projects/{project}/locations/{location}/ragCorpora/{ragCorpusId}
                full_name = corpus.name
                
                # Extract the corpus ID from the full resource name
                match = re.search(r'ragCorpora/(\d+)', full_name)
                
                if match:
                    return match.group(1)
                
                # Fallback: Return the last segment if regex fails
                return full_name.split('/')[-1]

        # If the loop completes without finding a match
        return ""

    except Exception as e:
        print(f"An error occurred while listing corpora: {e}")
        return ""

def upload_parent_directory(bucket_name: str, parent_dir: str, gcs_destination_folder: str = ""):
    global storage_client
    
    if not os.path.isdir(parent_dir):
        print(f"Error: Directory '{parent_dir}' does not exist.")
        return []

    try:
        bucket = storage_client.bucket(bucket_name)
    except Exception as e:
        print(f"Error accessing bucket '{bucket_name}': {e}")
        return []

    if gcs_destination_folder and not gcs_destination_folder.endswith('/'):
        gcs_destination_folder += '/'

    gcs_uris = []
    checksums = []
    
    for root, _, files in os.walk(parent_dir):
        for filename in files:
            local_file_path = os.path.join(root, filename)
            
            relative_path = os.path.relpath(local_file_path, parent_dir)
            md5_cs = hashlib.md5(open(local_file_path,'rb').read()).hexdigest()
            checksums.append(md5_cs)
            
            destination_blob_name = gcs_destination_folder + relative_path.replace(os.path.sep, "/")
            
            print(f"  -> Uploading '{relative_path}' to '{destination_blob_name}'...")
            
            blob = bucket.blob(destination_blob_name)
            
            blob.upload_from_filename(local_file_path)
            
            gcs_uris.append(f'gs://{bucket_name}/{destination_blob_name}')

    delete_folder_content(parent_dir)

    print(f"Synchronous upload complete. {len(gcs_uris)} files uploaded.")
    return gcs_uris, checksums

# to_upload = './scraped/'
# upload_parent_directory('regulatory_files', to_upload, os.path.basename(os.path.normpath(to_upload)))
#
def create_rag_corpus_and_import(corpus_name, gcs_uris):
    """Creates a Vertex AI RAG Corpus and imports files."""
    # 1. Create Corpus
    print(f"Creating RAG Corpus: {corpus_name}")
    embedding_model_config = RagEmbeddingModelConfig(
        vertex_prediction_endpoint=rag.VertexPredictionEndpoint(
            publisher_model="publishers/google/models/text-embedding-005"
        )
    )
    backend_config = RagVectorDbConfig(rag_embedding_model_config=embedding_model_config)
    
    try:
        rag_corpus = rag.create_corpus(
            display_name=corpus_name,
            backend_config=backend_config,
        )
        rag_corpus_name = rag_corpus.name
    except Exception as e:
        print(f"Error creating corpus: {e}")
        return None
        
    # 2. Import Files
    print(f"Importing files into RAG Corpus: {rag_corpus_name}")
    transformation_config = TransformationConfig(
        chunking_config=ChunkingConfig(chunk_size=512, chunk_overlap=100)
    )
    
    try:
        # Note: import_files is a long-running operation. 
        # For a production system, this should be done asynchronously (e.g., using Cloud Tasks/Pub/Sub).
        # We'll use a synchronous call for this example.
        rag.import_files(
            corpus_name=rag_corpus_name,
            paths=gcs_uris,
            transformation_config=transformation_config,
        )
        print("Import complete.")
        return True
    except Exception as e:
        print(f"Error importing files: {e}")
        return False

#
def create_corpus(corpus_name, link):

    doc_ref = db.collection(FIRESTORE_COLLECTION).document(corpus_name)

    initial_data = {
        "name": corpus_name,
        "link": link,
        "type": None,
        "pdf_links": [], # Will be updated after download
        "embeddings_available": False,
        "processing": True,
        "gcs_uris": [],
        "md5_checksums": []
    }
    doc_ref.set(initial_data)
   
    # 1. Check content type and determine PDF links
    is_pdf = check_pdf(link)

    doc_type = ""
   
    pdf_links_to_download = []
    if is_pdf:
        doc_type = 'pdf'
        pdf_links_to_download = [link]
    else:
        doc_type = 'webpage'
        pdf_links_to_download = find_regulatory_links_structured(link)
        
    # 2. Initial DB entry (as requested)
    
    # 3. Return initial response
    # For a real system, you would exit here and trigger a background job
    # to handle the rest of the processing.
    
    # --- ASYNCHRONOUS-LIKE PROCESS STARTS HERE ---
    
    # 4. Download PDFs to GCS and update pdf_links
    gcs_uris, checksums = upload_parent_directory(BUCKET_NAME, './temp', corpus_name)
    doc_ref.update({
        "type": doc_type,
        "pdf_links": pdf_links_to_download,
        "gcs_uris": gcs_uris,
        "md5_checksums": checksums
    })
    # downloaded_files_info = []
    # gcs_uris = []
    # for pdf_link in pdf_links_to_download:
        
        # file_info = download_and_store_pdf(pdf_link, corpus_name, BUCKET_NAME, storage_client)
        # downloaded_files_info.append(file_info)
        # gcs_uris.append(f"gs://{BUCKET_NAME}/{corpus_name}/{file_info['filename']}")
        
    # 5. Update DB with downloaded file info
    # doc_ref.update({"pdf_links": downloaded_files_info})
    
    # 6. Create RAG Corpus and import
    success = create_rag_corpus_and_import(corpus_name, gcs_uris)
    
    # 7. Final DB update
    final_data = {
        "processing": False,
        "embeddings_available": success
    }
    doc_ref.update(final_data)
    
    # --- ASYNCHRONOUS-LIKE PROCESS ENDS HERE ---
    
    # return jsonify({
    #     "message": "Corpus creation started/completed (synchronous process). Check database for final status.",
    #     "corpus_name": corpus_name,
    #     "status": doc_ref.get().to_dict()
    # }), 200

def update_corpus(corpus_name):
    doc_ref = db.collection(FIRESTORE_COLLECTION).document(corpus_name)
    corpus_data = doc_ref.get().to_dict()

    doc_ref.update({"processing": True, "embeddings_available": False})
    
    pdf_links_to_download = []
    if corpus_data['type'] == 'pdf':
        pdf_links_to_download = [corpus_data['link']]
        check_pdf(corpus_data['link'])
    else:
        pdf_links_to_download = find_regulatory_links_structured(corpus_data['link'])

    pdfs_paths = glob.glob(os.path.join(pdf_temp_save_path,'*.pdf'))
    new_checksums = set([hashlib.md5(open(pth,'rb').read()).hexdigest() for pth in pdfs_paths])
    if new_checksums == set(corpus_data['md5_checksums']):
        # no update requrired
        print('checksum match')
        delete_folder_content('./temp')
        doc_ref.update({"processing": False, "embeddings_available": True})
        return

    delete_directory_gcs(corpus_name)    

    gcs_uris, new_checksums = upload_parent_directory(BUCKET_NAME, './temp', corpus_name)
    doc_ref.update({
        "pdf_links": pdf_links_to_download,
        "gcs_uris": gcs_uris,
        "md5_checksums": new_checksums
    })
    delete_folder_content('./temp')

    rag.delete_corpus(f"projects/{PROJECT_ID}/locations/{VAI_REGION}/ragCorpora/{get_corpus_id_by_display_name(PROJECT_ID, VAI_REGION, corpus_name)}")
    success = create_rag_corpus_and_import(corpus_name, gcs_uris)
    
    # 7. Final DB update
    final_data = {
        "processing": False,
        "embeddings_available": success
    }
    doc_ref.update(final_data)
 
def delete_corpus(corpus_name):
    doc_ref = db.collection(FIRESTORE_COLLECTION).document(corpus_name)
    bucket = storage_client.bucket(BUCKET_NAME)
    blobs = bucket.list_blobs(prefix=f"{corpus_name}/")
    for blob in blobs:
        blob.delete()
    print(f"Files in GCS bucket folder '{corpus_name}' deleted.")
    rag.delete_corpus(f"projects/{PROJECT_ID}/locations/{VAI_REGION}/ragCorpora/{get_corpus_id_by_display_name(PROJECT_ID, VAI_REGION, corpus_name)}")
    doc_ref.delete()
    print('firestore record deleted')
 
# delete_corpus('GDPR')
import vertexai
from vertexai import rag
import os
import tempfile

CORPUS_NAME = "projects/gen-ai-hackathon-476616/locations/us-east4/ragCorpora/5044031582654955520"
# Path to the file you want to upload (local path or GCS URI)
# FILE_PATH = "gs://regulatory_files/Temp/Jaydev's TPM Resume.pdf"
FILE_PATH = "/home/larshinux/Downloads/Jaydev's TPM Resume.pdf"
# If using a local file, ensure it exists!

# --- 2. INITIALIZATION ---
# vertexai.init(project=PROJECT_ID, location=VAI_REGION)

# --- 3. UPLOAD FILE AND GET RESPONSE ---
try:
    files_pager = rag.list_files(corpus_name=CORPUS_NAME)
    print(files_pager)
    # print(f"Attempting to upload file: {FILE_PATH} to corpus: {CORPUS_NAME}")

    # The rag.upload_file function uploads the file, creates embeddings,
    # and returns the RagFile resource object.
    # rag_file_response = rag.upload_file(
    #     corpus_name=CORPUS_NAME,
    #     path=FILE_PATH,
    #     display_name='test jaydev w.pdf', # Use the filename as the display name
    #     description="Uploaded via Python SDK example."
    # )
    # rag_file_response = rag.import_files(
    #     corpus_name=CORPUS_NAME,
    #     paths=[FILE_PATH],
    #     transformation_config=TransformationConfig(
    #         chunking_config=ChunkingConfig(chunk_size=1024, chunk_overlap=200)
    #     ),
    # )
 
    # The full response object (RagFile) is printed here
    # print("\n✅ Full RagFile Upload Response Object:")
    # print(rag_file_response)

    # print("\n--- Extracted Full rag_file_id ---")
    # The 'name' field holds the full resource name, which is the full rag_file_id.
    # rag_file_resource_names = [file.name for file in rag_file_response.imported_rag_files]
    # print(f"Full rag_file_id: {rag_file_resource_names}")

except Exception as e:
    print(f"\n❌ An error occurred during file upload: {e}")
 
#
# create_corpus('DPDP', "https://www.dpdpa.in/dpdpa_rules_2025/dpdpa_draft_rules_english_.pdf")
# create_corpus('GDPR', "https://gdpr-info.eu/")

# corpora_pager = rag.list_corpora()
#
# corpora_list = list(corpora_pager)
#
# if not corpora_list:
#     print("No RAG corpuses found in this location.")
# else:
#     for corpus in corpora_list:
#         print(f"--------------------------------------------------")
#         print(f"Display Name: {corpus.display_name}")
#         print(f"Resource Name: {corpus.name}")
#         # print(f"Creation Time: {corpus.create_time.isoformat()}")
#     print(f"\nTotal Corpora Found: {len(corpora_list)}")
