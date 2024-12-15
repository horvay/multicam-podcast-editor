import os
import subprocess
from typing import Dict, List

import audalign as ad
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


def analyze(vid_list, align_videos=True, skip_bitrate_sync=False, threads=10):
    print("list of vids found to process" + str(vid_list))

    ######### private functions ##############

    def _padd_video_by(vid: VideoClip, padding: float):
        silent_audio = vid.audio.subclip(0, padding)  # pyright: ignore

        blank_clip = ColorClip(size=vid.size, color=(0, 0, 0), duration=padding)
        blank_clip = blank_clip.set_audio(silent_audio)

        return concatenate_videoclips([blank_clip, vid])

    def _volume(array1):
        return np.sqrt(((1.0 * array1) ** 2).mean())

    def cleanup_second():
        if os.path.exists("temp/list.txt"):
            os.remove("temp/list.txt")

        if os.path.exists("temp/second.mp4"):
            os.remove("temp/second.mp4")

    def _add_second_to(file: str):
        cleanup_second()
        # first add a second to the main video because sometimes it doesn't start first
        command = f"ffmpeg -i {file} -t 1 -c:v copy temp/second.mp4"
        subprocess.run(command, shell=True)

        with open("temp/list.txt", "w") as filelist:
            filelist.writelines(["file second.mp4\n", "file ../" + file])

        command = f"ffmpeg -f concat -safe 0 -i temp/list.txt -c copy temp/output.mp4 && mv temp/output.mp4 {file}"
        subprocess.run(command, shell=True)
        cleanup_second()

    #################################

    _add_second_to(vid_list[0])

    if os.path.exists("temp/temp_video.mp4"):
        os.remove("temp/temp_video.mp4")

    if not skip_bitrate_sync:
        for vid in vid_list:
            command = f"ffmpeg -threads {threads} -filter_threads {threads} -filter_complex_threads {threads} -i {vid} -c:v copy -b:a 128k -ar 44100 -frame_size 1024 temp/temp_video.mp4 && mv temp/temp_video.mp4 {vid}"
            subprocess.run(command, shell=True)

    print("finished making all bit rates the same")

    vids: List[VideoClip] = []

    for vid in vid_list:
        vids.append(VideoFileClip(vid))

    print("videos loaded")

    if align_videos:
        #####################################################
        ### padd the person clips to align them to main vid #
        #####################################################

        correlation_rec = ad.CorrelationRecognizer()
        result: Dict[str, float] = ad.target_align(  # pyright: ignore
            vid_list[0], "./inputfiles", recognizer=correlation_rec
        )
        print(result)

        for vid_index, vid in enumerate(vid_list):
            if vid_index == 0:
                vids[vid_index] = vids[vid_index].subclip(1)  # pyright: ignore
                continue

            padding = result[vid.replace("inputfiles/", "")]
            print("will pad " + str(padding) + " seconds to " + vid)

            vids[vid_index] = _padd_video_by(vids[vid_index], padding).subclip(1)  # pyright: ignore

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

            total_vol = _volume(sum(vol)) / 5
            new_volume.append(total_vol)
            # print("vid_clips now has this many elements: " + str(len(vid_clips)))
            x = x + 5

        average_volumes.append(new_volume)
        print(f"finished analyzing volume for video {i}")

    print("finished chunking audio into 5 second average segments")

    return vids, average_volumes
