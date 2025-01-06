from glob import glob
from moviepy import CompositeVideoClip, ImageClip, VideoFileClip, vfx
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
