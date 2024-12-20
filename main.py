import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import httpx
import openai
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Configuration
LINKUP_API_KEY = os.getenv("LINKUP_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
openai.api_key = OPENAI_API_KEY

class SearchQuery(BaseModel):
    query: str

class SearchResponse(BaseModel):
    answer: str
    sources: List[str]

@app.post("/search", response_model=SearchResponse)
async def search(search_query: SearchQuery):
    try:
        logger.info(f"Received search query: {search_query.query}")

        # Prepare the payload for Linkup API
        linkup_payload = {
            "depth": "standard",
            "outputType": "searchResults",
            "q": search_query.query
        }
        
        # Step 1: Search using Linkup
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=30.0,    # 30-second connection timeout
                    read=120.0,      # 2-minute read timeout
                    write=30.0,      # 30-second write timeout
                    pool=30.0        # 30-second pool timeout
                )
            ) as client:
                logger.info("Attempting to send request to Linkup API...")
                
                # Log start time
                import time
                start_time = time.time()
                
                linkup_response = await client.post(
                    "https://api.linkup.so/v1/search",
                    headers={
                        "Authorization": f"Bearer {LINKUP_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json=linkup_payload
                )
                
                # Log request duration
                request_duration = time.time() - start_time
                logger.info(f"Linkup API request took {request_duration:.2f} seconds")
            
            # Print out response details
            logger.info(f"Response Status Code: {linkup_response.status_code}")
            logger.info(f"Response Headers: {linkup_response.headers}")

            # Raise an exception for bad HTTP responses
            linkup_response.raise_for_status()
            
            response_data = linkup_response.json()
        
        except Exception as e:
            # More detailed error logging
            logger.error(f"Full error details: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            
            raise HTTPException(status_code=500, detail=f"Linkup API request failed: {str(e)}")

        # Check if we have results
        if not response_data.get('results'):
            logger.warning("No results found in Linkup response")
            raise HTTPException(
                status_code=404,
                detail="No search results found"
            )

        # Log the number of results
        total_results = len(response_data['results'])
        logger.info(f"Processing all {total_results} results from Linkup")

        # Extract relevant information from search results
        context = ""
        sources = []
        
        # Process ALL results
        for i, result in enumerate(response_data['results'], 1):
            if isinstance(result, dict):
                name = result.get('name', '')
                content = result.get('content', '')
                url = result.get('url', '')
                
                context += f"\nSource {i}: {name}\n"
                context += f"Content: {content}\n"
                sources.append(url)

        logger.info(f"Processed {len(sources)} sources. Total context length: {len(context)} characters")

        # Step 2: Analyze with OpenAI
        try:
            prompt = f"""Based on the following search results, provide a comprehensive answer to the query: "{search_query.query}"

Search Results:
{context}

Please provide a detailed answer that:
1. Is based strictly on the provided search results
2. References specific sources when presenting information
3. Uses bullet points where it helps clarity
4. Is well-structured and easy to read
5. Only includes information found in the given context

Keep your answer focused and informative, and make sure every statement can be traced back to the provided sources."""

            completion = openai.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that provides accurate and informative answers. Your goal is to answer questions using only the context provided to you. Always reference specific sources in your answer, and never mention things that are not included in the given context. Use bullet points when appropriate to structure your answer in a user-friendly way, but only if it enhances clarity."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000
            )

            answer = completion.choices[0].message.content
            logger.info("Successfully generated answer from OpenAI")
            
            return SearchResponse(
                answer=answer,
                sources=sources
            )
        
        except Exception as openai_error:
            logger.error(f"OpenAI API error: {openai_error}")
            raise HTTPException(
                status_code=500,
                detail=f"OpenAI processing error: {openai_error}"
            )

    except Exception as general_error:
        logger.error(f"Unexpected error in search endpoint: {general_error}")
        raise HTTPException(status_code=500, detail=str(general_error))