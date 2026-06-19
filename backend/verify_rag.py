import os
import sys
import time
import requests
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("verify_rag")

BASE_URL = "http://localhost:8000"

def create_sample_policy_file() -> str:
    """Create a sample enterprise policy file with specific facts."""
    filename = "hcltech_policy_2026.txt"
    content = (
        "HCLTECH ENTERPRISE OPERATION POLICIES 2026\n"
        "-----------------------------------------\n"
        "Policy 101 - Remote Work Arrangement:\n"
        "The standard remote work policy at HCLTech in 2026 permits employees to work up to 3 days from home per week, "
        "requiring explicit approval from their line manager. Team alignment sessions are mandatory on Mondays.\n\n"
        "Policy 102 - Corporate Travel Thresholds:\n"
        "All corporate travel expenses must be submitted for pre-authorization if the estimated cost of the trip "
        "exceeds $500. Trips under this amount do not require prior budget sign-off but must conform to travel guides.\n\n"
        "Policy 103 - Wellness Allowance Benefits:\n"
        "Employees are eligible for a monthly wellness stipend of $120. This benefit can be spent exclusively on gym memberships, "
        "nutrition consultation, or verified mental health applications.\n\n"
        "Policy 104 - Annual Innovation Hackathon:\n"
        "The annual HCLTech Hackathon is scheduled to run from October 12 to October 14, 2026. The grand prize is set at "
        "$10,000 for the winning team that designs the most innovative agentic AI workflow.\n\n"
        "Policy 105 - Cybersecurity Password Guidelines:\n"
        "Corporate password changes are strictly required every 90 days. Passwords must be at least 16 characters long "
        "and contain at least one special symbol, one number, and one uppercase letter."
    )
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return filename

def main():
    logger.info("=" * 60)
    logger.info("  STARTING REAL-WORLD RAG E2E PIPELINE VERIFICATION")
    logger.info("=" * 60)
    
    # 1. Create file
    filename = create_sample_policy_file()
    logger.info(f"Created sample policy file: {filename}")
    
    try:
        # 2. Upload file using API
        logger.info("Uploading policy file to backend upload API...")
        upload_url = f"{BASE_URL}/api/documents/upload"
        with open(filename, "rb") as f:
            files = {"file": (filename, f, "text/plain")}
            response = requests.post(upload_url, files=files)
            
        if response.status_code != 201:
            raise ValueError(f"Upload failed (status {response.status_code}): {response.text}")
            
        logger.info(f"Upload Succeeded: {response.json()}")
        
        # Give DB a brief moment to settle
        time.sleep(1)
        
        # 3. Formulate 5 questions
        questions = [
            ("How many days of home-office does the HCLTech 2026 policy allow?", "3 days"),
            ("What is the cost threshold for pre-authorizing business travel expenses?", "$500"),
            ("What can employees spend their wellness stipend on and how much is it?", "$120"),
            ("When is the annual HCLTech hackathon in 2026 and what is the grand prize?", "October 12 to October 14, 2026"),
            ("What are the corporate password requirements?", "16 characters")
        ]
        
        rag_results = []
        
        # 4. Query Chat API for each question
        chat_url = f"{BASE_URL}/api/chat/query"
        for idx, (question, keyword) in enumerate(questions):
            logger.info(f"Query {idx + 1}/5: '{question}'")
            
            payload = {
                "message": question,
                "history": []
            }
            
            chat_response = requests.post(chat_url, json=payload)
            if chat_response.status_code != 200:
                raise ValueError(f"Chat query failed (status {chat_response.status_code}): {chat_response.text}")
                
            data = chat_response.json()
            answer = data["response"]
            sources = data["sources"]
            
            logger.info(f"Answer: {answer}")
            logger.info(f"Sources: {sources}")
            logger.info("-" * 60)
            
            # Grounding check (does it contain expected keywords?)
            grounded = keyword.lower() in answer.lower()
            
            rag_results.append({
                "query": question,
                "answer": answer,
                "sources": sources,
                "grounded": grounded
            })
            
        # 5. Clean up document from backend and disk
        logger.info("Purging test document from vector database and storage...")
        delete_url = f"{BASE_URL}/api/documents/{filename}"
        del_response = requests.delete(delete_url)
        logger.info(f"Delete response: {del_response.json()}")
        
        if os.path.exists(filename):
            os.remove(filename)
            
        # 6. Save results to verification file
        report_data = {
            "timestamp": time.time(),
            "results": rag_results
        }
        with open("verify_rag_results.json", "w", encoding="utf-8") as rf:
            json.dump(report_data, rf, indent=2)
            
        logger.info("Verification complete. Generating validation report...")
        
    except Exception as e:
        logger.error(f"E2E Pipeline Failure: {e}", exc_info=True)
        if os.path.exists(filename):
            os.remove(filename)
        sys.exit(1)

if __name__ == "__main__":
    main()
