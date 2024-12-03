import math
import subprocess
from typing import List

from tprint import print_decorator

# import moviepy.video.fx.all as vfx
from moviepy.editor import (
    CompositeAudioClip,
    CompositeVideoClip,
    VideoClip,
    concatenate_videoclips,
)


print = print_decorator(print)


def shortcut(
    vids: List[VideoClip],
    average_volumes: List[List[float]],
    start: int,
    till: int,
    enable_jumpcuts=True,
    threads=10,
):
    till = till or (start + 60)

    people_vols = average_volumes[1:]
    people = vids[1:]

    final_clips: List[VideoClip] = []

    start_interval = math.floor(start / 5)
    end_interval = math.ceil(till / 5)

    # going through every 5 seconds of the audio clips.
    for i in range(start_interval, end_interval):
        sec = i * 5
        n_sec = sec + 5

        vols = [xvol[i] for xvol in people_vols]

        sorted_vols = sorted(enumerate(vols), key=lambda x: x[1], reverse=True)

        top_indices = [index for index, _ in sorted_vols[:2]]
        vid1: VideoClip = people[top_indices[0]].subclip(sec, n_sec)  # pyright: ignore
        vid2 = None

        print(f"comparing {sorted_vols[0][1]} to {sorted_vols[1][1]}")
        if len(top_indices) > 1 and sorted_vols[0][1] * 0.08 < sorted_vols[1][1]:
            vid2 = people[top_indices[1]].subclip(sec, n_sec)

        if vid2 is None:
            vid1 = vid1.resize(height=1920)  # pyright: ignore
            vid1 = vid1.set_position(("center", "top"))  # pyright: ignore
            new_clip = CompositeVideoClip([vid1], size=(1080, 1920))

        else:
            vid1 = vid1.resize(height=960)  # pyright: ignore
            vid1 = vid1.set_position(("center", "top"))  # pyright: ignore
            vid2 = vid2.resize(height=960)  # pyright: ignore
            vid2 = vid2.set_position(("center", "bottom"))  # pyright: ignore
            new_clip = CompositeVideoClip([vid1, vid2], size=(1080, 1920))

        print(f"Iteration {i} using {"one" if vid2 is None else "two"} video")
        final_clips.append(new_clip)

    final = concatenate_videoclips(final_clips)
    final_audio = CompositeAudioClip(
        [v.subclip(start_interval * 5, end_interval * 5).audio for v in people]  # pyright: ignore
    )

    final2: VideoClip = final.set_audio((final_audio))  # pyright: ignore
    final2.write_videofile(
        "short.mp4", threads=threads, codec="libx264", preset="slow", bitrate="3000k"
    )

    if enable_jumpcuts:
        command = (
            "auto-editor short.mp4 --margin 0.2sec --no-open "
            "--extras '-c:v libx264 -preset slow -b:v 3000k -maxrate 3000k -bufsize 6000k'"
        )

        subprocess.run(command, shell=True)
