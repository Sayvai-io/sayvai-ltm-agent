import httpx

url = "http://localhost:8000/chat"
payload = {
    "question": "tell me about chennai",
    "user_id": "subash",
    "thread_id": "1"
}  # Replace with your actual POST data

try:
    with httpx.stream("POST", url, json=payload, timeout=None) as response:
        response.raise_for_status()  # Check for HTTP errors
        print("Streaming response received. Processing chunks...\n")
        
        # Process chunks of the streaming response
        for chunk in response.iter_raw():
            print('......................')
          
            if chunk:  # Avoid printing empty chunks
                print(chunk.decode("utf-8"))
            print('......................')
except httpx.RequestError as e:
    print(f"An error occurred while making the request: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
