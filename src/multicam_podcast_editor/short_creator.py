import math
from typing import List

from multicam_podcast_editor.tprint import print_decorator
from moviepy import (
    CompositeAudioClip,
    CompositeVideoClip,
    VideoClip,
    concatenate_videoclips,
)

print = print_decorator(print)


def shortcut(
    vids: List[VideoClip],
    average_volumes: List[List[float]],
    short_start: float,
    till: float | None,
    threads: int = 10,
    output_name: str = "final",
):
    till = till or (short_start + 60)

    people_vols = average_volumes[1:]
    people = vids[1:]

    final_clips: List[VideoClip] = []

    start_interval = math.floor(short_start / 5)
    end_interval = math.ceil(till / 5)

    padd_start = short_start - start_interval * 5
    padd_end = end_interval * 5 - till

    # Going through every 5 seconds of the audio clips
    for i in range(start_interval, end_interval):
        sec = i * 5
        n_sec = sec + 5

        vols = [xvol[i] for xvol in people_vols]
        sorted_vols = sorted(enumerate(vols), key=lambda x: x[1], reverse=True)

        top_indices = [index for index, _ in sorted_vols[:2]]
        vid1: VideoClip = people[top_indices[0]].subclipped(sec, n_sec)  # pyright: ignore
        vid2 = None

        print(f"comparing {sorted_vols[0][1]} to {sorted_vols[1][1]}")
        if len(top_indices) > 1 and sorted_vols[0][1] * 0.08 < sorted_vols[1][1]:
            vid2 = people[top_indices[1]].subclipped(sec, n_sec)

        if vid2 is None:
            vid1 = vid1.resized(height=1920)  # pyright: ignore
            vid1 = vid1.with_position(("center", "top"))  # pyright: ignore
            new_clip = CompositeVideoClip([vid1], size=(1080, 1920))
        else:
            vid1 = vid1.resized(height=960)  # pyright: ignore
            vid1 = vid1.with_position(("center", "top"))  # pyright: ignore
            vid2 = vid2.resized(height=960)  # pyright: ignore
            vid2 = vid2.with_position(("center", "bottom"))  # pyright: ignore
            new_clip = CompositeVideoClip([vid1, vid2], size=(1080, 1920))

        print(f"Iteration {i} using {'one' if vid2 is None else 'two'} video")
        final_clips.append(new_clip)

    final = concatenate_videoclips(final_clips)
    final_audio = CompositeAudioClip(
        [v.subclipped(start_interval * 5, end_interval * 5).audio for v in people]
    )

    final2 = final.with_audio(final_audio)
    print(f"padding the video by {padd_start} and {-padd_end}")
    final2: VideoClip = final2.subclipped(
        padd_start, -padd_end if padd_end > 0 else None
    )

    output_path = f"output/{output_name}.mp4"
    final2.write_videofile(
        output_path,
        threads=threads,
        codec="libx264",
        preset="slow",
        bitrate="3000k",
    )
    print(f"Short saved to {output_path}")
