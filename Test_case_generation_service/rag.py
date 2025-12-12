from google import genai
from google.genai import types
from google.genai.errors import APIError
import vertexai
from vertexai import rag

# --- Configuration (Update these values) ---
PROJECT_ID = "gen-ai-hackathon-476616"
VAI_REGION = "us-east4"
LLM_MODEL_NAME = "gemini-2.5-flash"  # A fast, capable model for text generation
MASTER_RAG_CORPUS = "projects/gen-ai-hackathon-476616/locations/us-east4/ragCorpora/5044031582654955520"

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=VAI_REGION)
client = genai.Client(vertexai=True, project=PROJECT_ID, location=VAI_REGION)

top_k_chunks = 3  # Specify how many of the most relevant chunks to retrieve

rag_retrieval_config = rag.RagRetrievalConfig(
    top_k=top_k_chunks,
    # Optional: you can add a filter here if needed, e.g., for vector distance threshold
    # filter=rag.utils.resources.Filter(vector_distance_threshold=0.5),
)


rag_corpora = rag.get_corpus(name=MASTER_RAG_CORPUS)
# ----------------------------------------------------------------------
# 1. ROBUST PROMPT DRAFT
# ----------------------------------------------------------------------
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


# --- Example Usage ---
if __name__ == "__main__":
    
    # The requirement from the developer/tester
    user_requirement = (
        "The system must automatically delete all patient identifying information "
        "six months after the last billing interaction unless an active "
        "audit or legal hold is in place."
    )
    
    print("-" * 50)
    
    # Execute the process
    retrieved_context = retrieve_regulations(user_requirement)
    
    print(retrieved_context)

