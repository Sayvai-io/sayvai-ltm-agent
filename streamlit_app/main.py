import streamlit as st
import requests
from streamlit.runtime.scriptrunner import add_script_run_ctx
from threading import Thread

# Define the FastAPI URL
FASTAPI_URL = "http://travis-backend/chat"

def stream_response(user_id: str, question: str, thread_id: str, chat_output):
    """Fetch and display streaming response from the FastAPI server."""
    try:
        response = requests.post(
            FASTAPI_URL,
            json={"user_id": user_id, "question": question, "thread_id": thread_id},
            stream=True,
        )
        response.raise_for_status()

        # Display the streaming response
        chat_output.markdown("### Response:")
        full_response = ""
        for chunk in response.iter_content(chunk_size=512):
            if chunk:
                text = chunk.decode("utf-8")
                full_response += text
                chat_output.markdown(full_response)

    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred: {e}")

def main():
    """Main function to run the Streamlit application."""
    # Streamlit app title and layout
    st.set_page_config(page_title="Travis AI", layout="centered")
    st.title("Travis AI")
    st.markdown("### Chat with Travis AI in real-time")

    # Sidebar for user switching
    st.sidebar.markdown("## User Settings")
    user_id = st.sidebar.text_input("User ID", value="1")
    thread_id = st.sidebar.text_input("Thread ID", value="1")

    # Input area for user question
    question = st.text_input("😇:")

    # Chat output
    chat_output = st.empty()

    # Send button
    if st.button("Send Question"):
        if not question.strip():
            st.warning("Please enter a question before sending.")
        else:
            # Run streaming in a separate thread
            thread = Thread(target=stream_response, args=(user_id, question, thread_id, chat_output))
            add_script_run_ctx(thread)
            thread.start()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Powered by Sayvai Software LLP")

if __name__ == "__main__":
    main()
