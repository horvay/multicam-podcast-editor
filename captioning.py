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
    "came",
    "come",
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


# This is because whisper's start time is not reliable and is sometimes way too early
def _word_timing_adjusted(word: WordTranscript):
    start = float(word["start"])
    end = float(word["end"])
    duration = end - start
    if duration > 1.2:
        start = end - 1.2

    return start, end


def _get_positon_param(pos_param: str):
    coordinates = pos_param.split(",")
    if len(coordinates) != 2:
        raise Exception(
            "invalid position parameter. Must be two values separated by a comma with the whole thing in quotes"
        )
    try:
        x, y = int(coordinates[0]), int(coordinates[1])
    except ValueError:
        raise Exception("coordinates must be integers")

    return (x, y)


def transcribe_file(file: str):
    video = VideoFileClip(file)
    video.audio.write_audiofile("temp/temp.wav")  # pyright: ignore

    device = "cuda" if torch.cuda.is_available() else "cpu"

    model = WhisperModel("large-v3", device, compute_type="float32")
    segments, _ = model.transcribe(
        "temp/temp.wav",
        suppress_tokens=[],
        language="en",
        # vad_filter=True,
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
    font_size: int,
    caption_position: str,
    caption_type: int = 1,
):
    # @@@@@ private functions #######

    def _create_font_autoresize(size: int, word: str, max_width: int = 9999999):
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
                size=(None, size),
                margin=(13, 0),
                font_size=size * modifier,
                color="white",
            )

            if clip.size[0] < max_width:
                break

        assert clip is not None
        return clip

    ################################

    with open(file + ".csv", mode="r") as csvfile:
        reader = csv.DictReader(csvfile)
        transcription: List[WordTranscript] = list(reader)  # pyright: ignore

    video = VideoFileClip(file)

    text_clips: List[Clip.Clip] = []

    if caption_type == 1:
        if caption_position is None or caption_position == "":
            xpos, ypos = video.size[0] * 0.1, video.size[1] * 0.1
        else:
            xpos, ypos = _get_positon_param(caption_position)

        template_width = video.size[0] - xpos
        current_line_clips: List[TextClip] = []
        x = xpos
        for word in transcription:
            clip = _create_font_autoresize(font_size, word["word"])
            clip = TextClip(
                font,
                text=word["word"],
                method="label",
                stroke_color="black",
                stroke_width=5,
                size=(None, font_size + 8),
                margin=(0, 10),
                font_size=font_size,
                color="white",
            )

            start, _ = _word_timing_adjusted(word)

            if x + clip.size[0] > template_width:
                x = xpos
                for textclip in current_line_clips:
                    text_clips.append(
                        textclip.with_duration(
                            start - textclip.start + 0.5
                        ).with_effects(
                            [
                                vfx.CrossFadeIn(0.5),
                                vfx.CrossFadeOut(0.3),
                            ]
                        )
                    )

                current_line_clips = []

            position = (x + 10, ypos)
            clip: TextClip = clip.with_position(position).with_start(start)
            clip.size = (clip.size[0], clip.size[1] * 2)
            current_line_clips.append(clip)
            x = x + clip.size[0]

    if caption_type == 2:
        if video.size[0] > video.size[1]:
            width, height = int(video.size[0] * 0.3), int(video.size[1] * 0.34)
        else:
            width, height = int(video.size[0] * 0.6), int(video.size[1] * 0.33)

        font_max = font_size * 2
        fonts = [int(font_max * 0.45), int(font_max * 0.65), font_max]

        y = 0
        x = 0
        current_line: List[TextClip] = []

        def _new_font_size(word: str):
            rand = random.random()
            if word.lower() in AVOID_LIST:
                # print(f"avoided {text} since it is common")
                return fonts[0] if rand < 0.6 else fonts[1]
            else:
                return fonts[0] if rand < 0.4 else fonts[1] if rand < 0.65 else fonts[2]

        if caption_position is None or caption_position == "":
            xpos, ypos = 220, 60
        else:
            xpos, ypos = _get_positon_param(caption_position)

        new_font_size = fonts[1]
        for word in transcription:
            text = word["word"].strip()

            start, _ = _word_timing_adjusted(word)
            clip = _create_font_autoresize(new_font_size, text, width)

            reset = False
            if x > 0:  # always print text if at the beginnig of line
                if x + clip.size[0] > width:
                    y = y + clip.size[1] + 5
                    x = 0
                    new_font_size = _new_font_size(text)
                    clip = _create_font_autoresize(new_font_size, text, width)

                if y + clip.size[1] > height:
                    reset = True

                if reset:
                    for line_clip in current_line:
                        text_clips.append(
                            line_clip.with_duration(
                                start - line_clip.start + 0.7
                            ).with_effects(
                                [
                                    vfx.CrossFadeIn(0.5),
                                    vfx.CrossFadeOut(0.5),
                                ]
                            )
                        )

                    current_line = []
                    x, y = 0, 0
                    new_font_size = _new_font_size(text)
                    clip = _create_font_autoresize(new_font_size, text, width)

            clip = clip.with_position((x + xpos, y + ypos)).with_start(start)
            x = x + clip.size[0]
            current_line.append(clip)

    else:
        raise Exception("Not supported caption type")

    video_with_text = CompositeVideoClip([video] + text_clips)
    video_with_text.write_videofile("output/output_sentence.mp4")
