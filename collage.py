import os
import random
from glob import glob
from typing import List

from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    VideoFileClip,
    afx,
    vfx,
)
from moviepy.Clip import np
import numpy


def _apply_vignette(image: numpy.ndarray):
    H, W, _ = image.shape
    sigma = max(H, W) / 6
    center_i, center_j = H // 2, W // 2
    i, j = np.mgrid[0:H, 0:W]
    distance = np.sqrt((i - center_i) ** 2 + (j - center_j) ** 2)
    mask = np.exp(-(distance**2) / (2 * sigma**2))
    return (image * mask[:, :, np.newaxis]).astype(image.dtype)


def populate_file_with_images(input_vid: str, image_dir: str, output: str):
    vid = VideoFileClip(input_vid)
    images = glob(f"{image_dir}/*.png") + glob(f"{image_dir}/*.jpg")
    assert len(images) > 0, "no images found! (motherlicker)"
    image_time: float = vid.duration / len(images)

    random_images = sorted(images, key=lambda _: int(random.random() * 1000))
    print(f"found and randomized these images {random_images}")

    image_clips: list[ImageClip] = [
        ImageClip(img=random_images[x], duration=image_time)
        .image_transform(_apply_vignette)
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
    final.write_videofile(f"output/{output}.mp4")


def create_music_video(
    music_location: str,
    art_location: str,
    output: str,
    reminder_loc: str | None,
    thumbnail: str,
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
        .image_transform(_apply_vignette)
        .with_start(x * image_time)
        .with_effects(
            [
                vfx.CrossFadeIn(2.0),
                vfx.CrossFadeOut(2.0),
            ]
        )
        for x in range(0, len(random_images))
    ]

    if thumbnail != "":
        image_clips.insert(
            0,
            ImageClip(img=thumbnail, duration=1.5)
            .resized((1920, 1080))
            .with_effects([vfx.CrossFadeOut(1.0)])
            .with_start(0),
        )

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
    final.write_videofile(f"output/{output}.mp4")

    temp_files = glob("*TEMP_MPY_wvf_snd.mp3")
    for file in temp_files:
        os.unlink(file)
