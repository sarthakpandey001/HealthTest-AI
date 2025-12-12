# import urllib.parse
import hashlib
from flask import Flask, request, jsonify
import threading
from google.cloud import firestore 
import corpus_operations as co # Import the refactored logic
from corpus_operations import FIRESTORE_COLLECTION, db # Import necessary constants/clients
from flask_cors import CORS
import os
import json
import requests
from jira_ops import create_jira_issue_logic

app = Flask(__name__)
CORS(app) # This line enables CORS for your entire application# --- API ROUTES ---

@app.route('/create-jira-issues', methods=['POST'])
def handle_create_issues():
    """
    Flask route to receive a list of test cases and call the creation logic.
    """
    # Ensure the request contains JSON data
    if not request.is_json:
        return jsonify({"message": "Missing JSON in request"}), 400

    test_cases = request.get_json()

    # Ensure the JSON data is a list
    if not isinstance(test_cases, list):
        return jsonify({"message": "Request body must be a list of test case objects"}), 400
    
    # Run the core logic
    creation_results = create_jira_issue_logic(test_cases)
    
    # Return a consolidated result
    return jsonify({
        "message": f"Attempted to process {len(test_cases)} test case(s).",
        "results": creation_results
    }), 200

@app.route('/rag', methods=['POST'])
def invoke_rag():
    data = request.get_json()
    reqs = data.get('requirement')
    if not reqs:
        return jsonify({"message": "Missing 'requirement'"}), 400
    retrieved_docs = co.retrieve_regulations(reqs)
    return jsonify(retrieved_docs), 200

@app.route('/source-code', methods=['POST'])
def create_source_code_embeddings():
    """
    Endpoint to create a new RAG corpus.
    Initial DB entry and immediate 202 response, then background processing.
    """
    data = request.get_json()
    link = data.get('link')

    if  not link:
        return jsonify({"message": "Missing 'link' in request."}), 400

    doc_id = hashlib.sha256(link.encode('utf-8')).hexdigest()
    doc_ref = db.collection(FIRESTORE_COLLECTION).document(doc_id)

    if doc_ref.get().exists:
        return jsonify({"message": f"Corpus '{link}' already exists. Use PUT to update."}), 409

    # 1. Initial synchronous DB entry
    initial_data = {
        "name": link.split('/')[-1],
        "link": link,
        "type": 'source code', # Will be determined asynchronously
        "pdf_links": [], 
        "rag_file_ids": [],
        "embeddings_available": False,
        "processing": True,
        "gcs_uris": [],
        "md5_checksums": [],
        "created_at": firestore.SERVER_TIMESTAMP,
        "updated_at": firestore.SERVER_TIMESTAMP
    }
    doc_ref.set(initial_data)
    response_data = initial_data.copy() 

#    Replace the Sentinel objects with a JSON-serializable placeholder (e.g., a string)
    del response_data["created_at"]
    del response_data["updated_at"]

    # 2. Start the long-running task in a new thread
    thread = threading.Thread(
        target=co.create_source_code_embdeeings, 
        args=(link,)
    )
    thread.start()

    # 3. Return immediate response
    return jsonify({
        "message": "Corpus creation started in background.",
        "corpus_name": link,
        "initial_status": response_data
    }), 202


@app.route('/corpus', methods=['POST'])
def create_corpus():
    """
    Endpoint to create a new RAG corpus.
    Initial DB entry and immediate 202 response, then background processing.
    """
    data = request.get_json()
    corpus_name = data.get('corpus_name')
    link = data.get('link')

    if not corpus_name or not link:
        return jsonify({"message": "Missing 'corpus_name' or 'link' in request."}), 400

    doc_ref = db.collection(FIRESTORE_COLLECTION).document(corpus_name)
    if doc_ref.get().exists:
        return jsonify({"message": f"Corpus '{corpus_name}' already exists. Use PUT to update."}), 409

    # 1. Initial synchronous DB entry
    initial_data = {
        "name": corpus_name,
        "link": link,
        "type": None, # Will be determined asynchronously
        "pdf_links": [], 
        "rag_file_ids": [],
        "embeddings_available": False,
        "processing": True,
        "gcs_uris": [],
        "md5_checksums": [],
        "created_at": firestore.SERVER_TIMESTAMP,
        "updated_at": firestore.SERVER_TIMESTAMP
    }
    doc_ref.set(initial_data)
    response_data = initial_data.copy() 

#    Replace the Sentinel objects with a JSON-serializable placeholder (e.g., a string)
    del response_data["created_at"]
    del response_data["updated_at"]

    # 2. Start the long-running task in a new thread
    thread = threading.Thread(
        target=co.create_corpus_async_task, 
        args=(corpus_name, link)
    )
    thread.start()

    # 3. Return immediate response
    return jsonify({
        "message": "Corpus creation started in background.",
        "corpus_name": corpus_name,
        "status_check_url": f"/corpus/{corpus_name}",
        "initial_status": response_data
    }), 202


@app.route('/corpus/<corpus_name>', methods=['PUT'])
def update_corpus(corpus_name):
    """
    Endpoint to update an existing RAG corpus.
    Immediate 202 response, then background processing.
    """
    doc_ref = db.collection(FIRESTORE_COLLECTION).document(corpus_name)
    doc = doc_ref.get()

    if not doc.exists:
        return jsonify({"message": f"Corpus '{corpus_name}' not found."}), 404
        
    current_data = doc.to_dict()
    link = current_data.get('link') # Use the existing link for re-scrape/update check

    if current_data.get('processing'):
        return jsonify({"message": f"Corpus '{corpus_name}' is already being processed."}), 409

    # 1. Update status synchronously
    doc_ref.update({
        "processing": True,
        "embeddings_available": False,
        "updated_at": firestore.SERVER_TIMESTAMP
    })

    # 2. Start the long-running task in a new thread
    thread = threading.Thread(
        target=co.update_corpus_async_task, 
        args=(corpus_name, link)
    )
    thread.start()

    # 3. Return immediate response
    return jsonify({
        "message": "Corpus update started in background. Check back later for final status.",
        "corpus_name": corpus_name,
        "status_check_url": f"/corpus/{corpus_name}",
        "updated_status": doc_ref.get().to_dict() # Return the 'processing: true' state
    }), 202


@app.route('/corpus/<corpus_name>', methods=['DELETE'])
def delete_corpus_api(corpus_name):
    """
    Endpoint to delete a RAG corpus and all associated resources.
    This operation is performed synchronously as it's generally fast enough.
    """
    doc_ref = db.collection(FIRESTORE_COLLECTION).document(corpus_name)
    if not doc_ref.get().exists:
        return jsonify({"message": f"Corpus '{corpus_name}' not found."}), 404

    # The deletion task is synchronous but handles multiple resource types
    success = co.delete_corpus_sync_task(corpus_name)

    if success:
        return jsonify({
            "message": f"Corpus '{corpus_name}' and all associated resources (Firestore, GCS, Vertex AI RAG Corpus) deleted successfully."
        }), 200
    else:
        return jsonify({
            "message": f"Error deleting corpus '{corpus_name}'. Check server logs for details."
        }), 500

@app.route('/source-code', methods=['DELETE'])
def delete_source_code_corpus_api():
    """
    Endpoint to delete a RAG corpus and all associated resources.
    This operation is performed synchronously as it's generally fast enough.
    """
    data = request.get_json()
    link = data.get('link')

    # doc_id = urllib.parse.quote(link)
    doc_id = hashlib.sha256(link.encode('utf-8')).hexdigest()
    doc_ref = db.collection(FIRESTORE_COLLECTION).document(doc_id)

    if not doc_ref.get().exists:
        return jsonify({"message": f"Source code '{link}' not found."}), 404

    # The deletion task is synchronous but handles multiple resource types
    success = co.delete_source_code_embeddings(link)

    if success:
        return jsonify({
            "message": f"Source code corpus '{link}' and all associated resources (Firestore, GCS, Vertex AI RAG Corpus) deleted successfully."
        }), 200
    else:
        return jsonify({
            "message": f"Error deleting source code corpus '{link}'. Check server logs for details."
        }), 500


@app.route('/corpus/<corpus_name>', methods=['GET'])
def get_corpus_status(corpus_name):
    """
    Endpoint to check the status of a corpus.
    """
    doc_ref = db.collection(FIRESTORE_COLLECTION).document(corpus_name)
    doc = doc_ref.get()

    if not doc.exists:
        return jsonify({"message": f"Corpus '{corpus_name}' not found."}), 404
    
    return jsonify(doc.to_dict()), 200


@app.route('/corpus', methods=['GET'])
def list_corpuses():
    """
    Endpoint to list all corpuses in Firestore.
    """
    try:
        corpuses = [doc.to_dict() for doc in db.collection(FIRESTORE_COLLECTION).stream()]
        return jsonify(corpuses), 200
    except Exception as e:
        return jsonify({"message": f"Error listing corpuses: {e}"}), 500


if __name__ == '__main__':
    # Add a note about the importance of running the Flask app in a thread-safe manner
    # when using global state (like the selenium driver) in a production setting.
    # app.run(debug=True)
    app.run(debug=False, port=8080)
