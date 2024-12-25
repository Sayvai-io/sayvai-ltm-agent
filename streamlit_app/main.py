import streamlit as st
import requests
from threading import Thread
import logging

# Set up logger
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
)

# Define the FastAPI URL
FASTAPI_URL = "http://travis-backend/chat"


def stream_response(user_id: str, question: str, thread_id: str, chat_output):
    """Fetch and display streaming response from the FastAPI server."""
    logging.info("Starting stream_response function")
    logging.debug(f"Parameters - user_id: {user_id}, thread_id: {thread_id}, question: {question}")

    try:
        # Log before sending request
        logging.info(f"Sending POST request to {FASTAPI_URL}")

        response = requests.post(
            FASTAPI_URL,
            json={"user_id": user_id, "question": question, "thread_id": thread_id},
            stream=True,
        )
        response.raise_for_status()  # Raise an error for HTTP failures

        # Log successful connection
        logging.info("Successfully connected to the backend and started receiving data.")

        # Initialize the response string
        full_response = ""

        # Read and process chunks
        for chunk in response.iter_content(chunk_size=512):
            if chunk:
                text = chunk.decode("utf-8")
                full_response += text

                # Log each chunk received
                logging.debug(f"Received chunk: {text.strip()}")
                chat_output.markdown(f"**Travis AI:** {full_response}")  # Update UI

        # Log completion of streaming
        logging.info("Streaming complete. Full response received.")

    except requests.exceptions.RequestException as e:
        # Log exceptions
        logging.error(f"An error occurred while streaming: {e}")
        chat_output.error(f"An error occurred: {e}")


def main():
    """Main function to run the Streamlit application."""
    logging.info("Starting main function")

    # Streamlit app title and layout
    st.set_page_config(page_title="Travis AI", layout="centered")
    st.title("Travis AI")
    st.markdown("### Chat with Travis AI in real-time")
    logging.info("Streamlit UI initialized")

    # Sidebar for user settings
    st.sidebar.markdown("## User Settings")
    user_id = st.sidebar.text_input("User ID", value="Sanjaypranav")
    thread_id = st.sidebar.text_input("Thread ID", value="1")
    logging.debug(f"User settings - user_id: {user_id}, thread_id: {thread_id}")

    # Input area for user question
    question = st.text_input("😇:")
    logging.info("Question input field displayed")

    # Placeholder for chat output
    chat_output = st.empty()
    logging.info("Chat output placeholder initialized")

    # Send button
    if st.button("Send Question"):
        logging.info("Send button clicked")

        if not question.strip():
            st.warning("Please enter a question before sending.")
            logging.warning("Empty question submitted. Warning displayed to the user.")
        else:
            logging.info("Valid question submitted. Starting streaming thread.")

            # Run streaming in a background thread
            thread = Thread(target=stream_response, args=(user_id, question, thread_id, chat_output))
            thread.start()
            logging.info("Streaming thread started.")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Powered by Sayvai Software LLP")
    logging.info("Sidebar rendered")


if __name__ == "__main__":
    logging.info("Starting the Travis AI application")
    main()
