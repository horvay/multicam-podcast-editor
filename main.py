import glob
import json
import math
import os
import subprocess
from typing import List

import numpy as np
from moviepy.editor import (
    AudioClip,
    ColorClip,
    VideoClip,
    VideoFileClip,
    concatenate_videoclips,
)

files = glob.glob("person*.mp4") + glob.glob("*webcam*.mp4")
screenshares = glob.glob("*screen*.mp4")
vid_list = ["main.mp4"] + files

print("list of vids found to process" + str(vid_list))
print("list of vids screen shares to reduce focus on: " + str(screenshares))

vids: List[VideoClip] = []

reduced_focus_times = []
for _, ss in enumerate(screenshares):
    import re

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


def volume(array1):
    return np.sqrt(((1.0 * array1) ** 2).mean())


for vid in vid_list:
    video = VideoFileClip(vid)
    vids.append(video)

print("videos loaded")

#########################################
### padd the person clips to align them #
#########################################
# command = " ".join(["alignment_info_by_sound_track --json"] + vid_list)
command = " ".join(["alignment_info_by_sound_track --clear_cache --json"] + vid_list)

process = subprocess.Popen(
    command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
)
stdout, stderr = process.communicate()

json_data = json.loads(stdout.decode("utf-8"))
for item in json_data["edit_list"]:
    filename: str = os.path.basename(item[0])

    if filename == "main.mp4":
        continue

    padding: float = item[1]["pad"]
    print("will pad " + str(padding) + " seconds to " + filename)

    vid_index = vid_list.index(filename)
    video_clip = vids[vid_index]
    blank_clip = ColorClip(size=video_clip.size, color=(0, 0, 0), duration=padding)
    print("before: " + str(vids[vid_index].audio.duration))  # pyright: ignore
    vids[vid_index] = concatenate_videoclips([blank_clip, video_clip])
    print("after: " + str(vids[vid_index].audio.duration))  # pyright: ignore

### if the video ends early, extend it.
# reference_duration = vids[0].duration
# for i in range(1, len(vids)):
#     if vids[i].duration < reference_duration:
#         delta = reference_duration - vids[i].duration
#         print("adding " + str(delta) + " seconds to clip " + str(i))
#         blank_clip = ColorClip(size=vids[i].size, color=(0, 0, 0), duration=delta)
#         print("before: " + str(vids[i].audio.duration))  # pyright: ignore
#         vids[i] = concatenate_videoclips([vids[i], blank_clip])
#         print("after: " + str(vids[i].audio.duration))  # pyright: ignore

print("finish syncing based on audio")

average_volumes = []
maxes = []
for vid in vids:
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

print("finished chunking audio into 5 second average segments")


def roundup(x):
    return int(math.ceil(x / 5.00)) * 5


# clips = []

# x = 0
# y = 0
# todo: do this as part of determining focus to save lots of time
# for vid in vids:
#     vid_duration = roundup(vid.duration) - 5
#     vid_clips = []
#
#     x = 0
#     while x <= vid_duration:
#         newclip = vid.subclip(x, x + 5)
#         vid_clips.append(newclip)
#         # print("vid_clips now has this many elements: " + str(len(vid_clips)))
#         x = x + 5
#
#     if x < vid.duration:
#         newclip = vid.subclip(x, vid.duration - x)
#         vid_clips.append(newclip)
#
#     clips.append(vid_clips)

# print("finished breaking up vid clips into 5 second chunks")

secondsDiviedBy5: int = math.ceil(vids[0].audio.duration / 5)  # pyright: ignore
main = vids[0]

people_vols = average_volumes[1:]
people = vids[1:]

final_clips: List[VideoClip] = [main.subclip(0, 5)]  # pyright: ignore
unfocused_count: int = 0


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
            is_added = True
            break

    if is_added:
        continue

    for x, xvol in enumerate(people_vols):
        is_louder = True
        if n_sec > people[x].duration:
            continue

        for y, yvol in enumerate(people_vols):
            if y == x:
                continue
            if len(yvol) > i and len(xvol) > i and xvol[i] * 0.1 < yvol[i]:
                is_louder = False
                break

        if is_louder:
            print("interval " + str(i) + " had person " + str(x) + " greater vol")
            final_clips.append(
                people[x].subclip(  # pyright: ignore
                    sec,
                    n_sec if people[x].duration > n_sec else people[x].duration,
                )
            )
            is_added = True
            unfocused_count = 0
            break

    if is_added:
        continue

    print("interval " + str(i) + " had no greater person vol")
    final_clips.append(
        main.subclip(sec, n_sec if main.duration > n_sec else main.duration)  # pyright: ignore
    )
    unfocused_count = unfocused_count + 1


final = concatenate_videoclips(final_clips)

# finalAudio = CompositeAudioClip([v.audio for v in vids[1:]]) # TODO didn't work - no idea why
final2 = final.set_audio(vids[0].audio)
final2.write_videofile(  # pyright: ignore
    "multicam-podcast.mp4", audio_bitrate="1000k", bitrate="4000k"
)

command = "auto-editor multicam-podcast.mp4 --margin 0.4sec --no-open -q -c:v h264"
subprocess.run(command, shell=True)

command = "ffmpeg -i multicam-podcast_ALTERED.mp4 -q:v 0 final.mp4"
subprocess.run(command, shell=True)
