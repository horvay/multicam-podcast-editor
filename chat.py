import os
from ollama import chat
from ollama import ChatResponse


def chat_with_transcript(question, model="llama3.2-vision"):
    if not os.path.exists("transcript.txt"):
        print("Either provide a transcript.txt file or use -t to generate one.")
        return

    with open("transcript.txt", "r") as file:
        chat_log = file.read()

    response: ChatResponse = chat(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are an AI assistent specializing in analyzing transcripts of podcast and providing useful information for youtube titles, descriptions, and chapters",
            },
            {
                "role": "user",
                "content": f"Here is a transcript of a podcast episode: \n```\n{chat_log}\n```\n\n{question}",
            },
        ],
    )

    print(response["message"]["content"])
