from glob import glob
from typing import List
from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    VideoFileClip,
    vfx,
    afx,
)
import random


def populate_file_with_images(input_vid: str, image_dir: str):
    vid = VideoFileClip(input_vid)
    images = glob(f"{image_dir}/*.png") + glob(f"{image_dir}/*.jpg")
    assert len(images) > 0, "no images found! (motherlicker)"
    image_time: float = vid.duration / len(images)

    random_images = sorted(images, key=lambda _: int(random.random() * 1000))
    print(f"found and randomized these images {random_images}")

    image_clips: list[ImageClip] = [
        ImageClip(img=random_images[x], duration=image_time)
        .with_start(x * image_time)
        .with_effects(
            [
                vfx.CrossFadeIn(1.0),
                vfx.CrossFadeOut(1.0),
            ]
        )
        for x in range(0, len(random_images))
    ]

    print("Finished scheduling image clips")

    final = CompositeVideoClip([vid] + image_clips)
    final.write_videofile("output/final.mp4")


def create_music_video(
    music_location: str, art_location: str, reminder_loc: str | None
):
    songs = glob(f"{music_location}/*.mp3")
    assert len(songs) > 0, "No MP3 files found in music directory!"
    random_songs = sorted(songs, key=lambda _: int(random.random() * 1000))

    audio_clips = [
        AudioFileClip(path).with_effects([afx.AudioFadeIn(1.0), afx.AudioFadeOut(3.0)])
        for path in random_songs
    ]

    current_start: float = 0.0
    for index, audio_clip in enumerate(audio_clips):
        audio_clips[index] = audio_clip.with_start(current_start)
        assert isinstance(
            audio_clip.duration, float
        ), "duration wasn't a folat??? NAAANNIIII"
        current_start = current_start + audio_clip.duration - 1  # 1sec crossover

    images = glob(f"{art_location}/*.png") + glob(f"{art_location}/*.jpg")
    assert len(images) > 0, "No image files found in art directory!"
    random_images = sorted(images, key=lambda _: int(random.random() * 1000))

    total_duration = current_start + 1
    image_time = total_duration / len(random_images)

    image_clips: list[ImageClip] = [
        ImageClip(img=random_images[x], duration=image_time)
        .with_start(x * image_time)
        .with_effects(
            [
                vfx.CrossFadeIn(1.0),
                vfx.CrossFadeOut(1.0),
            ]
        )
        for x in range(0, len(random_images))
    ]

    reminder_clips: List[ImageClip] = []
    if reminder_loc is not None:
        reminders = glob(f"{reminder_loc}/*.png")
        for start in range(1, int(total_duration), 120):
            for index, reminder in enumerate(reminders):
                reminder_clips.append(
                    ImageClip(img=reminder, duration=5)
                    .with_start(start + index * 5)
                    .with_effects([vfx.CrossFadeIn(1.0), vfx.CrossFadeOut(1.0)])
                )

    audio = CompositeAudioClip(audio_clips)
    final = CompositeVideoClip(image_clips + reminder_clips, size=(1920, 1080))
    final = final.with_audio(audio)
    final = final.with_fps(24)
    final.write_videofile("output/final.mp4")
