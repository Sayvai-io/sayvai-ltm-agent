import streamlit as st
import requests
import threading
import logging
import queue
import time

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)


def init_state():
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'response_queue' not in st.session_state:
        st.session_state.response_queue = queue.Queue()
    if 'is_processing' not in st.session_state:
        st.session_state.is_processing = False


def fetch_response(user_id: str, question: str, thread_id: str, response_queue: queue.Queue):
    try:
        response = requests.post(
            "http://travis-backend:8000/chat",
            json={"user_id": user_id, "question": question, "thread_id": thread_id}
        )
        response.raise_for_status()
        response_queue.put(response.text)
    except Exception as e:
        logging.error(f"Error fetching response: {e}")
        response_queue.put(f"Error: {str(e)}")
    finally:
        st.session_state.is_processing = False


def main():
    st.set_page_config(page_title="Travis AI")
    init_state()
    st.title("Travis AI")

    with st.sidebar:
        user_id = st.text_input("User ID", "Sanjaypranav")
        thread_id = st.text_input("Thread ID", "1")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    try:
        if st.session_state.is_processing:
            response = st.session_state.response_queue.get_nowait()
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.is_processing = False
            st.rerun()
    except queue.Empty:
        if st.session_state.is_processing:
            time.sleep(0.1)
            st.rerun()

    if prompt := st.chat_input("Message Travis AI..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.is_processing = True

        thread = threading.Thread(
            target=fetch_response,
            args=(user_id, prompt, thread_id, st.session_state.response_queue),
            daemon=True
        )
        thread.start()
        st.rerun()


if __name__ == "__main__":
    main()