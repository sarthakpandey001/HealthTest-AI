from google import genai
import vertexai
from vertexai import rag
from vertexai.preview.generative_models import GenerativeModel, Tool

from rag import VAI_REGION

# --- Configuration ---
# TODO(developer): Update PROJECT_ID and LOCATION
MODEL_NAME = "gemini-2.5-flash"
PROJECT_ID = "gen-ai-hackathon-476616"
FIRESTORE_COLLECTION = "rag_corpuses"
LOCATION = "us-east4"

# Initialize Vertex AI API
vertexai.init(project=PROJECT_ID, location=LOCATION)

## 1. Get All RAG Corpora

try:
    print(f"🔍 Listing all RAG Corpora in {PROJECT_ID}/{LOCATION}...")
    
    # Get all RagCorpus objects
    all_corpora = rag.list_corpora()
    
    if not all_corpora:
        print("⚠️ No RAG Corpora found. Cannot create RAG tools.")
        exit()

    # print(f"✅ Found {len(all_corpora)} corpora.")
    # print(all_corpora)

except Exception as e:
    print(f"❌ An error occurred while listing corpora: {e}")
    exit()

# Dictionary to hold the created tools: {corpus_display_name: Tool_object}
multi_rag_tools = {}

for corpus in all_corpora:
    corpus_name = corpus.name
    display_name = corpus.display_name

    try:
        # Step A: Create a RagResource pointing to this single corpus
        rag_resource = rag.RagResource(rag_corpus=corpus_name)
        
        # Step B: Create a VertexRagStore containing only that single resource
        # This bypasses the "only support 1 RagResource" error
        vertex_rag_store = rag.VertexRagStore(
            rag_resources=[rag_resource] # Must be a list with one item
        )

        # Step C: Create the Tool object
        rag_tool = Tool.from_retrieval(
            retrieval=rag.Retrieval(source=vertex_rag_store)
        )
        
        # Store the tool using its display name (or resource name)
        multi_rag_tools[display_name] = rag_tool
        
        print(f"   -> Created tool for corpus: '{display_name}'")

    except Exception as e:
        print(f"   ❌ Failed to create tool for '{display_name}': {e}")
        continue

# Extract the list of Tool objects to pass to the model
tools_list = list(multi_rag_tools.values())
print(f"\n🛠️ Successfully created {len(tools_list)} distinct RAG Tool(s).")

print(f"\n🧠 Generating content with model {MODEL_NAME}...")

model = GenerativeModel(MODEL_NAME)
while True:
    prompt = input('prompt:\n')

# Pass the list of all created tools
    response = model.generate_content(
        prompt,
        tools=tools_list 
    )

    print("\n--- Model Response ---")
    print(response.text)

# The response metadata will show which tool(s) the model chose to use.
    print("\n--- Used Tools/Grounding ---")
# This shows the actual API call the model decided to make.
    if response.candidates and response.candidates[0].grounding_metadata:
        # This list will contain one entry for each RAG tool the model used
        used_resources = response.candidates[0].grounding_metadata.grounding_chunks
        print(f"Model used {len(used_resources)} RAG retrieval source(s).")
        # You would typically inspect the tool_calls or function_calls for more detail
        # but the grounding_metadata confirms the retrieval occurred.
    else:
        print("Model did not use any RAG tool for retrieval.")
# Initialize Vertex AI API
# vertexai.init(project=PROJECT_ID, location=LOCATION)
#
# ## 1. Get All RAG Corpora Resource Names
#
# try:
#     print(f"🔍 Listing all RAG Corpora in {PROJECT_ID}/{LOCATION}...")
#
#     # The rag.list_corpora() method retrieves all RagCorpus objects
#     all_corpora = rag.list_corpora()
#
#     # Extract the resource names (corpus.name) from all the objects
#     all_corpus_names = [corpus.name for corpus in all_corpora]
#
#     if not all_corpus_names:
#         print("⚠️ No RAG Corpora found. Cannot create RAG tool.")
#         exit()
#
#     print(f"✅ Found {len(all_corpus_names)} corpora. Resource names collected.")
#     # print("Collected Names:", all_corpus_names) # Uncomment to view all names
#
# except Exception as e:
#     print(f"❌ An error occurred while listing corpora: {e}")
#     exit()
#
# rag_resources = [
#     rag.RagResource(rag_corpus=name) 
#     for name in all_corpus_names
# ]
#
# # Define the VertexRagStore using all the collected resources
# vertex_rag_store = rag.VertexRagStore(
#     rag_resources=rag_resources
# )
#
# # Create the final Retrieval Tool
# rag_retrieval_tool = Tool.from_retrieval(
#     retrieval=rag.Retrieval(source=vertex_rag_store)
# )
#
# print(f"🛠️ RAG Tool created, encompassing {len(rag_resources)} corpora.")
#
# model = GenerativeModel(MODEL_NAME)
# prompt = "list all the regulation documents you have in context and compliance names"
#
# print(f"\n🧠 Generating content with model {MODEL_NAME}...")
# response = model.generate_content(
#     prompt,
#     tools=[rag_retrieval_tool]
# )
#
# print("\n--- Model Response ---")
# print(response.text)
#
# # You can inspect the grounding metadata to see which corpora/files were used
# # grounding_metadata = response.candidates[0].grounding_metadata
# # print("\nGrounding Metadata:", grounding_metadata)
