# Fastapi File


from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import StreamingResponse

from travis.agent import LongTermMemoryAgent

load_dotenv()


class ChatConfig(BaseModel):
    user_id: str 
    question: str
    thread_id: str 

app = FastAPI(
    title="Sayvai Test API",
    description="A test API for the Sayvai test.",
    version="0.1",
)

agent = LongTermMemoryAgent(model_name="gpt-4o-mini")
agent.build_graph()

@app.get("/")
def root():
    return {"message": "API working. Welcome to the Sayvai test API."}


@app.post("/chat")
def chat(item: ChatConfig):
    config = {"configurable": {"user_id": item.user_id, "thread_id": item.thread_id}}
    return StreamingResponse(agent.run(item.question, config))

@app.get("/health")
def health():
    return {"status": "healthy"}
    # return agent.run(item.question, config)

@app.post("/chatbot")
async def chat_endpoint(request: ChatConfig):
    def generate_chunks():
        yield """Hi again! What’s on your mind today?
        The communication between frontend and backend is working correctly. 
        The logs show successful POST requests with 200 status codes, 
        indicating proper data transmission.
        Would you like to enhance any specific aspect of 
        the application?Based on the image, I see the API endpoint is working and returning responses correctly. 
        The backend endpoint (/chat) accepts JSON data with user_id, question, and t
        hread_id fields and returns streamed responses.
        Would you like to implement any specific features like message persistence, typing indicators, 
        or response formatting?""".encode('utf-8')
    return StreamingResponse(generate_chunks())