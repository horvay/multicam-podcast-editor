import os
from ollama import chat


def chat_with_transcript(question, model="llama3.2-vision"):
    if not os.path.exists("input/transcript.txt"):
        print(
            "Either provide a transcript.txt file or use -t to generate one and place it in your inputfiles folder"
        )
        return

    with open("input/transcript.txt", "r") as file:
        chat_log = file.read()

    stream = chat(
        model=model,
        stream=True,
        messages=[
            {
                "role": "system",
                "content": "You are an AI assistent specializing in analyzing transcripts of podcast and providing useful information for youtube titles, descriptions, and chapters",
            },
            {
                "role": "user",
                "content": f"Here is a transcript of a podcast episode: \n\n```\n{chat_log}\n```\n\n{question}",
            },
        ],
    )

    for chunk in stream:
        print(chunk["message"]["content"], end="", flush=True)
