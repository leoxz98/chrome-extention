from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from config import settings
from langchain_utils import getResponse  

class TextRequest(BaseModel):
    text: str

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    print(f"Server running on port: {settings.PORT}")
    return {'message': 'API is running', 'status': 'ok'}

@app.post("/analyze")
async def analyze(req: TextRequest):
    user_text = req.text
    print(f"Texto recibido: {user_text}")
    print("\n  -------- \n")
    # Llamamos la función de LangChain
    analysis_result = getResponse(user_text)
    print(analysis_result)

    return {"result": analysis_result}


