# Fastapi File
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import StreamingResponse

from travis.agent import LongTermMemoryAgent

load_dotenv()


class ChatConfig(BaseModel):
    user_id: str = "1"
    question: str
    thread_id: str = "1"

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
    # return agent.run(item.question, config)


