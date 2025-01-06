import math
import re
import subprocess
from typing import List

from moviepy import (
    CompositeAudioClip,
    VideoClip,
    VideoFileClip,
    concatenate_videoclips,
)


def multicam(
    screenshares: List[str],
    enable_jumpcuts: bool,
    vids: List[VideoClip],
    average_volumes,
    res1080p=True,
    threads=10,
    output_name="final",
):
    print("list of vids screen shares to reduce focus on: " + str(screenshares))

    reduced_focus_times = []
    for _, ss in enumerate(screenshares):
        time_match = re.search(r"(\d+h_)?(\d+m_)?(\d+s_)?(\d+ms)", ss)

        if time_match:
            hours = int(time_match.group(1)[:-2] if time_match.group(1) else 0)
            minutes = int(time_match.group(2)[:-2] if time_match.group(2) else 0)
            seconds = int(time_match.group(3)[:-2] if time_match.group(3) else 0)
            milliseconds = int(time_match.group(4)[:-2] if time_match.group(4) else 0)

            start_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000

            ss_vid = VideoFileClip(ss)
            end_seconds = start_seconds + ss_vid.duration
            reduced_focus_times.append((start_seconds, end_seconds))

            print(
                f"creating less focused session from: {start_seconds:.2f} to: {end_seconds:.2f}"
            )
        else:
            print(f"Time format not found in the screen file {ss}")

    secondsDiviedBy5: int = math.ceil(vids[0].audio.duration / 5)  # pyright: ignore
    main: VideoClip = vids[0]

    people_vols = average_volumes[1:]
    people = vids[1:]

    final_clips: List[VideoClip] = [main.subclipped(0, 5)]
    unfocused_count: int = 0
    focused_count: int = 0

    def _add_subclip(sec: float, n_sec: float, vid: VideoClip):
        final_clips.append(
            vid.subclipped(sec, n_sec if vid.duration > n_sec else vid.duration)
        )

    # going through every 5 seconds of the audio clips.
    for i in range(1, secondsDiviedBy5):
        sec = i * 5
        n_sec = sec + 5

        # skip if in reduced focus times and we've been focused in the last 10 seconds
        if unfocused_count < 2 and any(
            start < sec < end for start, end in reduced_focus_times
        ):
            print(f"interval {i} unfocussing due to screenshare")
            _add_subclip(sec, n_sec, main)
            unfocused_count, focused_count = unfocused_count + 1, 0
            continue

        if focused_count < 2:
            current_iter_vols = [
                xvol[i] if len(xvol) > i else -100 for xvol in people_vols
            ]
            sorted_vols = sorted(
                enumerate(current_iter_vols), key=lambda x: x[1], reverse=True
            )

            first = sorted_vols[0]
            second = sorted_vols[1] if len(sorted_vols) > 1 else None
            print(
                f"comparing {first[1]} to {second[1] if second is not None else "None"}"
            )

            if second is None or first[1] * 0.05 > second[1]:  # pyright: ignore
                assert len(sorted_vols) > 0
                print(f"interval {str(i)} had person {str(first[0])} greater vol")
                _add_subclip(sec, n_sec, people[first[0]])
                unfocused_count, focused_count = 0, focused_count + 1
                continue

        print("interval " + str(i) + " had no greater person vol")
        _add_subclip(sec, n_sec, main)
        unfocused_count, focused_count = unfocused_count + 1, 0

    final = concatenate_videoclips(final_clips)

    finalAudio = CompositeAudioClip([v.audio for v in vids[1:]])
    final2: VideoClip = final.with_audio(finalAudio)
    final2.write_videofile(
        f"output/{output_name}.mp4",
        threads=threads,
        codec="libx264",
        audio_codec="aac",
        preset="slow",
        bitrate="3000k",
    )

    print(f"apply jumpcuts? {enable_jumpcuts}")
    if enable_jumpcuts:
        command = (
            f"auto-editor output/{output_name}.mp4 --margin 0.4sec --no-open "
            "--extras '-c:v libx264 -c:a aac -preset slow -b:v 3000k -maxrate 3000k -bufsize 6000k' "
            f"-o output/{output_name}-jumpcut.mp4"
        )

        if res1080p:
            command += " -res 1920,1080"

        subprocess.run(command, shell=True)
