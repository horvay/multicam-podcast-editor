import csv
import os
import random
from typing import List, TypedDict

import torch
from faster_whisper import WhisperModel
from moviepy import (
    Clip,
    CompositeVideoClip,
    TextClip,
    VideoFileClip,
    vfx,
)

AVOID_LIST = {
    "a",
    "about",
    "all",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "but",
    "by",
    "can",
    "could",
    "did",
    "do",
    "does",
    "for",
    "from",
    "had",
    "has",
    "have",
    "he",
    "her",
    "here",
    "him",
    "his",
    "how",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "like",
    "me",
    "more",
    "my",
    "no",
    "not",
    "of",
    "on",
    "one",
    "or",
    "our",
    "out",
    "she",
    "should",
    "so",
    "some",
    "than",
    "that",
    "the",
    "their",
    "them",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "to",
    "too",
    "up",
    "us",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "will",
    "with",
    "would",
    "you",
    "your",
    "am",
    "an",
    "are",
    "at",
    "be",
    "by",
    "did",
    "do",
    "go",
    "had",
    "has",
    "have",
    "he",
    "her",
    "him",
    "his",
    "i",
    "if",
    "in",
    "is",
    "it",
    "me",
    "my",
    "no",
    "not",
    "of",
    "on",
    "or",
    "so",
    "that",
    "this",
    "to",
    "up",
    "us",
    "we",
    "you",
}


class WordTranscript(TypedDict):
    start: float
    end: float
    probability: float
    word: str


def word_timing_adjusted(word: WordTranscript):
    start = float(word["start"])
    end = float(word["end"])
    duration = end - start
    if duration > 1.2:
        start = end - 1.2

    return start, end


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


def caption_video(
    file: str,
    font: str,
    caption_word_duration: float,
    font_size: int,
    caption_type: int = 1,
):
    with open(file + ".csv", mode="r") as csvfile:
        reader = csv.DictReader(csvfile)
        transcription: List[WordTranscript] = list(reader)  # pyright: ignore

    video = VideoFileClip(file)

    text_clips: List[Clip.Clip] = []

    if caption_type == 1:
        margin = video.size[0] * (0.1 if caption_word_duration <= 0 else 0.15)
        template_width = video.size[0] - margin
        current_line_clips: List[TextClip] = []
        x = margin
        for word in transcription:
            clip = TextClip(
                font,
                text=word["word"],
                method="label",
                stroke_color="black",
                stroke_width=5,
                margin=(0, 10),
                font_size=font_size,
                color="white",
            )

            start, _ = word_timing_adjusted(word)

            if x + clip.size[0] > template_width:
                x = margin
                for textclip in current_line_clips:
                    text_clips.append(
                        textclip.with_duration(  # pyright: ignore
                            start - textclip.start + 0.5
                            if caption_word_duration <= 0
                            else caption_word_duration
                        ).with_effects(  # pyright: ignore
                            [
                                vfx.CrossFadeIn(0.5),
                                vfx.CrossFadeOut(0.3),
                            ]
                        )
                    )

                current_line_clips = []

            position = (x + 10, video.size[1] * 0.1)
            clip: TextClip = (
                clip.with_position(position).with_start(start)  # pyright: ignore
            )
            clip.size = (clip.size[0], clip.size[1] * 2)
            current_line_clips.append(clip)
            x = x + clip.size[0]

    if caption_type == 2:
        if video.size[0] > video.size[1]:
            width, height = int(video.size[0] * 0.3), int(video.size[1] * 0.5)
        else:
            width, height = int(video.size[0] * 0.5), int(video.size[1] * 0.3)

        font_max = 120
        fonts = [int(font_max * 0.45), int(font_max * 0.65), font_max]

        def create_font(size: int, word: str, max_width: int):
            clip = None
            for i in range(10, -1, -1):
                modifier = i / 10
                clip = TextClip(
                    font,
                    text=word,
                    method="label",
                    stroke_color="black",
                    vertical_align="center",
                    stroke_width=5,
                    size=((None, size)),
                    margin=(13, 0),
                    font_size=size * modifier,
                    color="white",
                )

                if clip.size[0] < max_width:
                    break

            assert clip is not None
            return clip

        y = 0
        x = 0
        current_line: List[TextClip] = []

        def new_font_size(word: str):
            rand = random.random()
            if word.lower() in AVOID_LIST:
                # print(f"avoided {text} since it is common")
                return fonts[0] if rand < 0.6 else fonts[1]
            else:
                return fonts[0] if rand < 0.4 else fonts[1] if rand < 0.60 else fonts[2]

        font_size = fonts[1]
        for word in transcription:
            text = word["word"].strip()

            start, _ = word_timing_adjusted(word)

            clip = create_font(font_size, text, width)

            reset = False
            if x > 0:  # always print text if at the beginnig of line
                if x + clip.size[0] > width:
                    y = y + clip.size[1] + 5
                    x = 0
                    font_size = new_font_size(text)
                    clip = create_font(font_size, text, width)

                if y + clip.size[1] > height:
                    reset = True

                if reset:
                    for line_clip in current_line:
                        text_clips.append(
                            line_clip.with_duration(
                                start - line_clip.start + 0.7
                            ).with_effects(
                                [
                                    vfx.CrossFadeIn(1),
                                    vfx.CrossFadeOut(0.6),
                                ]
                            )
                        )

                    current_line = []
                    x, y = 0, 0
                    font_size = new_font_size(text)
                    clip = create_font(font_size, text, width)

            clip = clip.with_position((x + 100, y + 100)).with_start(start)
            x = x + clip.size[0]
            current_line.append(clip)

        # caption_container = CompositeVideoClip([container] + text_clips)
        # # caption_container.write_videofile("output/test.mp4", fps=video.fps)
        # text_clips = [
        #     caption_container.with_position(
        #         (int(video.size[0] * 0.1), int(video.size[1] * 0.1))
        #     )
        # ]

    else:
        raise Exception("Not supported caption type")

    video_with_text = CompositeVideoClip([video] + text_clips)
    video_with_text.write_videofile("output/output_sentence.mp4")
