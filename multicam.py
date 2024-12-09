import math
import re
import subprocess
from typing import List

from moviepy.editor import (
    CompositeAudioClip,
    VideoClip,
    VideoFileClip,
    concatenate_videoclips,
)


def multicam(
    screenshares, enable_jumpcuts, vids, average_volumes, res1080p=True, threads=10
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
    main = vids[0]

    people_vols = average_volumes[1:]
    people = vids[1:]

    final_clips: List[VideoClip] = [main.subclip(0, 5)]  # pyright: ignore
    unfocused_count: int = 0
    focused_count: int = 0

    # going through every 5 seconds of the audio clips.
    for i in range(1, secondsDiviedBy5):
        sec = i * 5
        n_sec = sec + 5
        is_added = False

        # skip if in reduced focus times and we've been focused in the last 10 seconds
        for start, end in reduced_focus_times:
            if unfocused_count < 2 and start < sec < end:
                print(f"interval {i} unfocussing due to screenshare")
                final_clips.append(
                    main.subclip(sec, n_sec if main.duration > n_sec else main.duration)  # pyright: ignore
                )
                unfocused_count = unfocused_count + 1
                focused_count = 0
                is_added = True
                break

        if is_added:
            continue

        if focused_count < 2:
            for x, xvol in enumerate(people_vols):
                is_louder = True
                if n_sec > people[x].duration:
                    continue

                for y, yvol in enumerate(people_vols):
                    if y == x:
                        continue
                    print(f"comparing higher vol {xvol[i]} to {yvol[i]}")
                    if len(yvol) > i and len(xvol) > i and xvol[i] * 0.05 < yvol[i]:
                        is_louder = False
                        break

                if is_louder:
                    print(
                        "interval " + str(i) + " had person " + str(x) + " greater vol"
                    )
                    final_clips.append(
                        people[x].subclip(  # pyright: ignore
                            sec,
                            n_sec if people[x].duration > n_sec else people[x].duration,
                        )
                    )
                    is_added = True
                    unfocused_count = 0
                    focused_count = focused_count + 1
                    break

        if is_added:
            continue

        print("interval " + str(i) + " had no greater person vol")
        final_clips.append(
            main.subclip(sec, n_sec if main.duration > n_sec else main.duration)  # pyright: ignore
        )
        unfocused_count = unfocused_count + 1
        focused_count = 0

    final = concatenate_videoclips(final_clips)

    finalAudio = CompositeAudioClip([v.audio for v in vids[1:]])
    final2: VideoClip = final.set_audio(finalAudio)  # pyright: ignore
    final2.write_videofile(  # pyright: ignore
        "final.mp4", threads=threads, codec="libx264", preset="slow", bitrate="3000k"
    )

    print(f"apply jumpcuts? {enable_jumpcuts}")
    if enable_jumpcuts:
        command = (
            "auto-editor final.mp4 --margin 0.4sec --no-open "
            "--extras '-c:v libx264 -preset slow -b:v 3000k -maxrate 3000k -bufsize 6000k'"
        )

        if res1080p:
            command += " -res 1920,1080"

        subprocess.run(command, shell=True)
