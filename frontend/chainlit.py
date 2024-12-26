import chainlit as cl
import requests
import json
import httpx
import asyncio

API_URL = "http://travis-backend:8000"

async def get_user_input():
    response = await cl.AskUserMessage(content="Please enter your user ID:", timeout=180).send()
    return response.get("content") if response else None

async def get_thread_input():
    response = await cl.AskUserMessage(content="Please enter your thread ID (or press Enter for new thread):", timeout=180).send()
    return response.get("content") if response else cl.user_session.id

@cl.on_chat_start
async def start():
    user_id = await get_user_input()
    thread_id = await get_thread_input()
    cl.user_session.set("user_id", user_id)
    cl.user_session.set("thread_id", thread_id)

@cl.on_message
async def main(message: cl.Message):
    data = {
        "user_id": str(cl.user_session.get("user_id")),
        "question": message.content,
        "thread_id": str(cl.user_session.get("thread_id"))
    }

    try:
        with httpx.stream("POST",f"{API_URL}/chat", json=data, timeout= None) as response:
            response.raise_for_status()
            msg = cl.Message(content="")
            async with cl.Step(name="Processing") as step:
                for chunk in response.iter_raw():
                    if chunk:
                        text = chunk.decode('utf-8')
                        msg.content = text
                        await msg.stream_token(text)

    except Exception as e:
        await cl.Message(content=f"Error: {str(e)}").send()

if __name__ == "__main__":
    cl.run()