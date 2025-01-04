import os
import re

import torch
from faster_whisper import WhisperModel
from moviepy import (
    VideoFileClip,
)


def transcribe(individuals, word_pause=1.0):
    print("list of vids found to transcribe " + str(individuals))

    def _extract_name(file_name):
        pattern = r"_-_\d-(.*)-webcam"
        match = re.search(pattern, file_name)
        if match:
            name = match.group(1)
            print(f"found name {name}")
            return name
        return None

    def _format_seconds(seconds):
        hours = int(seconds // 3600)
        seconds %= 3600
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)

        return f"{hours:02d}h {minutes:02d}m {seconds:02d}s"

    def _format_chat(entry):
        return f"[{_format_seconds(entry[1])}] {entry[0]}: {entry[3]}\n"

    transcription = []

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"using {device}")

    model = WhisperModel("large-v3", device)
    for i, vid in enumerate(individuals):
        print(f"transcribing video {vid}")
        name = _extract_name(vid) or f"Person{i}"

        video = VideoFileClip(vid)
        video.audio.write_audiofile("temp/temp.wav")  # pyright: ignore
        segments, _ = model.transcribe(
            "temp/temp.wav",
            suppress_tokens=[],
            vad_filter=True,
            vad_parameters={"speech_pad_ms": 1000},
            initial_prompt="transcribe the following and include a *laughing* when there is laughter'",
            condition_on_previous_text=True,
            log_progress=True,
            beam_size=5,
            word_timestamps=True,
            hotwords="laughing laugh laughter",
        )

        current_speech = [name, 0, 0, ""]
        for segment in segments:
            for word in segment.words or []:
                if word.end - current_speech[2] > word_pause:
                    if current_speech[3] != "":
                        transcription.append(current_speech)
                    # we use end as start since start isn't accurate
                    current_speech = [name, word.end - 0.5, word.end, word.word]
                else:
                    current_speech[3] += word.word
                    current_speech[2] = word.end

        if current_speech[3] != "":
            transcription.append(current_speech)
        print(f"finished transcribing {name}")
        os.remove("temp/temp.wav")

    transcription.sort(key=lambda x: x[1])

    with open("output/transcript.txt", "w") as file:
        for entry in transcription:
            file.write(_format_chat(entry))
