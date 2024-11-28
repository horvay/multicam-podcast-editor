from ollama import chat
from ollama import ChatResponse

with open("transcript.txt", "r") as file:
    chat_log = file.read()

print(
    f"Here is a transcript of a podcast episode: \n```\n{chat_log}\n```\nPlease provide useful chapters to set up in youtube with the chapter name and time of the chapter"
)
response: ChatResponse = chat(
    model="llama3.2",
    messages=[
        {
            "role": "system",
            "content": "You are an AI assistent specializing in analyzing transcripts of podcast and providing useful information for youtube titles, descriptions, and chapters",
        },
        {
            "role": "user",
            "content": f"Here is a transcript of a podcast episode: \n```\n{chat_log}\n```\nPlease provide useful chapters to set up in youtube with the chapter name and time of the chapter",
        },
    ],
)

print(response["message"]["content"])
