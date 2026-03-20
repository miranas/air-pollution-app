from fastapi import FastAPI
from pydantic import BaseModel
import requests
import json

app = FastAPI()


# Request, input model for API(what to expect in POST request)
class QueryRequest(BaseModel):
    prompt: str
    max_length: int = 100

# Response model for API (what will be returned as answer)
class QueryResponse(BaseModel):
    generated_text: str

# Api endpoint for text generation
@app.post("/api/phi", response_model=QueryResponse)
def ask_phi(query: QueryRequest):
    
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "phi3",
            "prompt": query.prompt,
            "options": {"num_predict": query.max_length}
        },
        stream=True
    )
    generated: str = ""
    for line in response.iter_lines(decode_unicode=True):
        if line:
            try:
                obj = json.loads(line)
                if "response" in obj:
                    generated += obj["response"]
            except Exception:
                continue
    return QueryResponse(generated_text=generated)
            

   