import os 
from dotenv import load_dotenv
import tempfile
from pathlib import Path
import PyPDF2  # To read PDF files

# Load environment variables before other imports
load_dotenv()

import chainlit as cl
from core.quivr_core import Brain
from core.quivr_core.brain.brain_defaults import default_llm
from core.quivr_core.storage.local_storage import LocalStorage

# Initialize storage
storage = LocalStorage()

# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text += page.extract_text()
    return text

# Function to clear the session (for uploading a new file)
async def clear_session():
    # Clear the brain and file path from the session
    cl.user_session.set("brain", None)
    cl.user_session.set("file_path", None)
    await cl.Message(content="The current file has been cleared. Please upload a new file.").send()

    # Restart the upload process
    await request_file_upload()

# Function to request a new file upload
async def request_file_upload():
    files = None

    # Prompt for a new file upload
    files = await cl.AskFileMessage(
        content="Please upload a file to begin! (Supported formats: .txt, .pdf)",
        accept=["text/plain", "application/pdf"],
        max_size_mb=20,
    ).send()

    # Check if the file was uploaded
    if not files or len(files) == 0:
        await cl.Message(content="No file uploaded. Please try again.").send()
        return

    file = files[0]
    msg = cl.Message(content=f"Processing `{file.name}`...")
    await msg.send()

    # Process the file based on its extension
    if file.name.endswith(".txt"):  # Text file
        with open(file.path, "r", encoding="utf-8") as f:
            text = f.read()
    elif file.name.endswith(".pdf"):  # PDF file
        text = extract_text_from_pdf(file.path)
    else:
        msg.content = "Unsupported file format!"
        await msg.update()
        return

    # Store the text in a temporary .txt file for further processing
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False
    ) as temp_file:
        temp_file.write(text)
        temp_file.flush()
        temp_file_path = temp_file.name

    brain = Brain.from_files(name="user_brain", file_paths=[temp_file_path])

    # Store the file path and brain in the session
    cl.user_session.set("file_path", temp_file_path)
    cl.user_session.set("brain", brain)

    # Let the user know that the system is ready
    msg.content = f"Processing `{file.name}` done. You can now ask questions!"
    await msg.update()

@cl.on_chat_start
async def on_chat_start():
    # Start the process by prompting for a file upload
    await request_file_upload()

@cl.on_message
async def main(message: cl.Message):
    # Check for the 'reset' command to clear the session and allow uploading a new file
    if message.content.lower() == 'reset':
        await clear_session()
        return

    brain = cl.user_session.get("brain")  # Retrieve the brain object

    if brain is None:
        await cl.Message(content="Please upload a file first.").send()
        return

    # Prepare the message for streaming
    msg = cl.Message(content="")
    await msg.send()

    try:
        # Use the ask_stream method for streaming responses
        async for chunk in brain.ask_streaming(message.content):
            await msg.stream_token(chunk.answer)

        await msg.send()
    except Exception as e:
        error_msg = cl.Message(content=f"Error: {str(e)}")
        await error_msg.send()

if __name__ == "__main__":
    print("Starting the chatbot...")
    # print(f"OPENAI_API_KEY is {'set' if os.getenv('OPENAI_API_KEY') else 'not set'}")
