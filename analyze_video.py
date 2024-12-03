import json
import os
import subprocess
from typing import List

from tprint import print_decorator
import numpy as np
from moviepy.editor import (
    AudioClip,
    ColorClip,
    VideoClip,
    VideoFileClip,
    concatenate_videoclips,
)

print = print_decorator(print)


def analyze(vid_list, align_videos=True, use_align_cache=True, skip_bitrate_sync=False):
    print("list of vids found to process" + str(vid_list))

    if os.path.exists("temp_video.mp4"):
        os.remove("temp_video.mp4")

    if not skip_bitrate_sync:
        for vid in vid_list:
            command = f"ffmpeg -i {vid} -c:v copy -b:a 128k -ar 44100 -frame_size 1024 temp_video.mp4 && mv temp_video.mp4 {vid}"
            subprocess.run(command, shell=True)

    print("finished making all bit rates the same")

    vids: List[VideoClip] = []

    def volume(array1):
        return np.sqrt(((1.0 * array1) ** 2).mean())

    for _, vid in enumerate(vid_list):
        video = VideoFileClip(vid)
        vids.append(video)

    print("videos loaded")

    if align_videos:
        #####################################################
        ### padd the person clips to align them to main vid #
        #####################################################
        if not use_align_cache:
            print("clearing cache before aligning videos")
            command = " ".join(
                ["alignment_info_by_sound_track --clear_cache --json"] + vid_list
            )
        else:
            print("using cache for aligning videos")
            command = " ".join(["alignment_info_by_sound_track --json"] + vid_list)

        process = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, _ = process.communicate()

        json_data = json.loads(stdout.decode("utf-8"))
        for item in json_data["edit_list"]:
            filename: str = os.path.basename(item[0])

            if filename == "main.mp4":
                continue

            padding: float = item[1]["pad"]
            print("will pad " + str(padding) + " seconds to " + filename)

            vid_index = vid_list.index(filename)
            video_clip = vids[vid_index]

            silent_audio = video_clip.audio.subclip(0, padding)  # pyright: ignore

            blank_clip = ColorClip(
                size=video_clip.size, color=(0, 0, 0), duration=padding
            )
            blank_clip = blank_clip.set_audio(silent_audio)

            print("before: " + str(vids[vid_index].audio.duration))  # pyright: ignore
            vids[vid_index] = concatenate_videoclips([blank_clip, video_clip])
            print("after: " + str(vids[vid_index].audio.duration))  # pyright: ignore

        print("finish syncing based on audio")

    print("Starting video chunking")
    average_volumes = []
    for i, vid in enumerate(vids):
        x = 0
        new_volume = []
        aud: AudioClip = vid.audio  # pyright: ignore
        while x <= aud.duration - 5:
            vol = (
                aud.subclip(x, x + 1).to_soundarray(fps=44100)  # pyright: ignore
                + aud.subclip(x + 1, x + 2).to_soundarray(fps=44100)  # pyright: ignore
                + aud.subclip(x + 2, x + 3).to_soundarray(fps=44100)  # pyright: ignore
                + aud.subclip(x + 3, x + 4).to_soundarray(fps=44100)  # pyright: ignore
                + aud.subclip(x + 4, x + 5).to_soundarray(fps=44100)  # pyright: ignore
            )

            total_vol = volume(sum(vol)) / 5
            new_volume.append(total_vol)
            # print("vid_clips now has this many elements: " + str(len(vid_clips)))
            x = x + 5

        average_volumes.append(new_volume)
        print(f"finished analyzing volume for video {i}")

    print("finished chunking audio into 5 second average segments")

    return vids, average_volumes
