import csv
import os
from typing import List, TypedDict

import torch
from faster_whisper import WhisperModel
from moviepy import (
    CompositeVideoClip,
    TextClip,
    VideoFileClip,
    vfx,
)


class WordTranscript(TypedDict):
    start: float
    end: float
    probability: float
    word: str


def transcribe_file(file: str):
    video = VideoFileClip(file)
    video.audio.write_audiofile("temp/temp.wav")  # pyright: ignore

    device = "cuda" if torch.cuda.is_available() else "cpu"

    model = WhisperModel("large-v3", device, compute_type="float32")
    segments, _ = model.transcribe(
        "temp/temp.wav",
        suppress_tokens=[],
        language="en",
        vad_filter=True,
        condition_on_previous_text=False,
        log_progress=True,
        beam_size=10,
        word_timestamps=True,
    )

    transcription: List[WordTranscript] = []
    for segment in segments:
        for word in segment.words or []:
            transcription.append(
                {
                    "start": word.start,
                    "end": word.end,
                    "probability": word.probability,
                    "word": word.word,
                }
            )

    filename = os.path.basename(file)
    with open(f"output/{filename}.csv", "w") as output:
        writer = csv.DictWriter(
            output, fieldnames=["start", "end", "probability", "word"]
        )
        writer.writeheader()
        writer.writerows(transcription)


def caption_video(file: str):
    with open(file + ".csv", mode="r") as csvfile:
        reader = csv.DictReader(csvfile)
        transcription: List[WordTranscript] = list(reader)  # pyright: ignore

    video = VideoFileClip(file)

    margin = video.size[0] * 0.1
    template_width = video.size[0] * 0.9
    text_clips = []
    current_line_clips: List[TextClip] = []
    current_width = margin
    for word in transcription:
        clip = TextClip(
            "/usr/share/fonts/opentype/urw-base35/NimbusMonoPS-Bold.otf",
            text=word["word"],
            method="label",
            stroke_color="black",
            stroke_width=5,
            margin=(0, 10),
            font_size=60,
            color="white",
        )

        if current_width + clip.size[0] > template_width:
            current_width = margin
            for textclip in current_line_clips:
                text_clips.append(
                    textclip.with_duration(  # pyright: ignore
                        float(word["start"]) - textclip.start + 0.5
                    ).with_effects(  # pyright: ignore
                        [
                            vfx.CrossFadeIn(0.5),
                            vfx.CrossFadeOut(0.3),
                        ]
                    )
                )

            current_line_clips = []

        position = (current_width + 10, video.size[1] * 0.1)
        clip: TextClip = (
            clip.with_position(position).with_start(word["start"])  # pyright: ignore
        )
        clip.size = (clip.size[0], clip.size[1] * 2)
        current_line_clips.append(clip)
        current_width = current_width + clip.size[0]

    video_with_text = CompositeVideoClip([video] + text_clips)
    video_with_text.write_videofile("output/output_sentence.mp4")
