import glob
import os
import re
import torch
from faster_whisper import WhisperModel
from moviepy.editor import (
    VideoFileClip,
)

vid_list = glob.glob("person*.mp4") + glob.glob("*webcam*.mp4")

print("list of vids found to process" + str(vid_list))


def extract_name(file_name):
    pattern = r"-([^-]+)-webcam.*\.mp4$"
    match = re.search(pattern, file_name)
    if match:
        return match.group(1)
    return None


def format_seconds(seconds):
    hours = int(seconds // 3600)
    seconds %= 3600
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)

    return f"{hours:02d}h {minutes:02d}m {seconds:02d}s"


print("finished making all bit rates the same")

transcription = []

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"using {device}")

model = WhisperModel("large-v3", device, compute_type="float16")
for i, vid in enumerate(vid_list):
    print(f"transcribing video {vid}")
    name = extract_name(vid) or f"Person{i}"

    video = VideoFileClip(vid)
    video.audio.write_audiofile("temp.mp3", codec="mp3", bitrate="192k")  # pyright: ignore
    segments, info = model.transcribe(
        "temp.mp3",
        suppress_tokens=[],
        vad_filter=True,
        condition_on_previous_text=False,
        beam_size=5,
        word_timestamps=True,
    )

    current_speech = [name, 0, 0, ""]
    for segment in segments:
        for word in segment.words or []:
            if word.end - current_speech[2] > 1:
                if current_speech[3] != "":
                    transcription.append(current_speech)
                # we use end as start since start isn't accurate
                current_speech = [name, word.end - 0.5, word.end, word.word]
            else:
                current_speech[3] += word.word
                current_speech[2] = word.end

            previous_end = word.end

    if current_speech[3] != "":
        transcription.append(current_speech)
    print(f"finished transcribing {name}")
    os.remove("temp.mp3")

transcription.sort(key=lambda x: x[1])

with open("transcript.txt", "w") as file:
    for entry in transcription:
        file.write(f"[{format_seconds(entry[1])}] {entry[0]}: {entry[3]}\n")
