import os
import shutil
import subprocess
from typing import Dict, List

import audalign as ad
from audalign.config.correlation_spectrogram import CorrelationSpectrogramConfig
from multicam_podcast_editor.tprint import print_decorator
from moviepy import (
    AudioClip,
    ColorClip,
    VideoClip,
    VideoFileClip,
    concatenate_videoclips,
)

print = print_decorator(print)


def analyze(
    vid_list: List[str],
    max_time: float,
    align_videos=True,
    skip_bitrate_sync=False,
    threads=10,
):
    print("list of vids found to process" + str(vid_list))

    ######### private functions ##############

    def _padd_video_by(vid: VideoClip, padding: float):
        blank_clip = ColorClip(size=vid.size, color=(0, 0, 0), duration=padding)
        vid = vid.with_start(padding)

        return concatenate_videoclips([blank_clip, vid])

    def cleanup_second():
        if os.path.exists("temp/list.txt"):
            os.remove("temp/list.txt")

        if os.path.exists("temp/second.mp4"):
            os.remove("temp/second.mp4")

    def _add_second_to(file: str):
        cleanup_second()
        # first add a second to the main video because sometimes it doesn't start first
        fp_file = os.path.abspath(file)

        command = f"ffmpeg -i '{fp_file}' -t 5 -c:v copy temp/second.mp4"
        print(f"running command {command}")
        subprocess.run(command, shell=True)

        with open("temp/list.txt", "w") as filelist:
            filelist.writelines(["file second.mp4\n", f"file '{fp_file}'"])

        fp_list = os.path.abspath("temp/list.txt")
        fp_output = os.path.abspath("temp/output.mp4")

        command = f"ffmpeg -f concat -safe 0 -i '{fp_list}' -c copy {fp_output}"
        print(f"running command {command}")
        subprocess.run(command, shell=True)

        shutil.move(fp_output, fp_file)
        cleanup_second()

    #################################

    _add_second_to(vid_list[0])

    if os.path.exists("temp/temp_video.mp4"):
        os.remove("temp/temp_video.mp4")

    print(f"syncing the bit rate of the f8ollowing: {vid_list}")
    if not skip_bitrate_sync:
        for vid in vid_list:
            fp_tempvid = os.path.abspath("temp/temp_video.mp4")

            command = f"ffmpeg -threads {threads} -filter_threads {threads} -filter_complex_threads {threads} -i '{os.path.abspath(vid)}' -c:v copy -b:a 128k -ar 44100 -frame_size 1024 {fp_tempvid}"
            print(f"running command {command}")
            subprocess.run(command, shell=True)

            shutil.move(fp_tempvid, vid)

    print("finished making all bit rates the same")

    if align_videos:
        #####################################################
        ### padd the person clips to align them to main vid #
        #####################################################

        config = CorrelationSpectrogramConfig()
        config.multiprocessing = False
        correlation_rec = ad.CorrelationSpectrogramRecognizer(config)

        result: Dict[str, float] = ad.target_align(  # pyright: ignore
            target_file=vid_list[0],
            directory_path="./temp",
            recognizer=correlation_rec,
        )

        print(result)

    # Keep track of how much padding was applied to each video so the multicam
    # step (which now relies exclusively on ffmpeg) can accurately map the
    # timestamps it generates back to the original source files. The first
    # entry corresponds to the main video which has no audio-sync padding
    # applied (only the 5 s duplicate that we remove later).
    paddings: list[float] = [0.0 for _ in vid_list]

    # Load the video clips via MoviePy for further volume analysis.
    vids: list[VideoClip] = [VideoFileClip(v) for v in vid_list]

    print("videos loaded")

    if align_videos:
        for vid_index, vid in enumerate(vid_list):
            if vid_index == 0:
                # Remove the duplicated 5-second intro that was added earlier for
                # safer ffmpeg concat syncing.
                vids[vid_index] = vids[vid_index].subclipped(5)
                continue

            padding = result[vid.replace("temp/", "")]  # pyright: ignore
            paddings[vid_index] = padding
            print(f"will pad {padding} seconds to {vid}")

            vids[vid_index] = _padd_video_by(vids[vid_index], padding).subclipped(5)

        print("finish syncing based on audio")

    print("Starting video chunking")
    average_volumes = []
    for i, vid in enumerate(vids):
        aud: AudioClip = vid.audio  # pyright: ignore
        new_volume = [
            aud.subclipped(x, x + 5).max_volume()
            for x in range(0, int(aud.duration - 5) + 1, 5)
        ]

        average_volumes.append(new_volume)
        print(f"finished analyzing volume for video {i}")

    print("finished chunking audio into 5 second average segments")

    return vids, average_volumes, paddings
