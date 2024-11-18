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

vid_list = [
    "main.mp4",
]

files = glob.glob("person*.mp4")
vid_list = vid_list + files
print("list of vids found to process" + str(vid_list))

vids: List[VideoClip] = []


def volume(array1):
    return np.sqrt(
        ((1.0 * array1) ** 2).mean()
    )  # fucntion returning the volume of inputted clip.


for vid in vid_list:
    video = VideoFileClip(vid)
    # print(video)/home/horvay/Documents/multicam-podcast-editor/intronewplayers.mp4 /home/horvay/Documents/multicam-podcast-editor/intronewplayers.mp4 /home/horvay/Documents/multicam-podcast-editor/intronewplayers.mp4 /home/horvay/Documents/multicam-podcast-editor/intronewplayers.mp4 /home/horvay/Downloads/person1.mp4 /home/horvay/Downloads/person2.mp4 /home/horvay/Downloads/person3.mp4 /home/horvay/Downloads/main.mp4
    vids.append(video)

print("videos loaded")

#########################################
### padd the person clips to align them #
#########################################
command = " ".join(["alignment_info_by_sound_track --json"] + vid_list)
# command = " ".join(["alignment_info_by_sound_track --clear_cache --json"] + vid_list)

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
reference_duration = vids[0].duration
for i in range(1, len(vids)):
    if vids[i].duration < reference_duration:
        delta = vids[0].duration - vids[i].duration
        print("adding " + str(delta) + " seconds to clip " + str(i))
        blank_clip = ColorClip(size=vids[i].size, color=(0, 0, 0), duration=delta)
        vids[i] = concatenate_videoclips([blank_clip, vids[i]])

print("finish syncing based on audio")

volumes = []
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


clips = []

x = 0
y = 0

for vid in vids:
    vid_duration = roundup(vid.duration) - 5
    vid_clips = []

    x = 0
    while x <= vid_duration:
        newclip = vid.subclip(x, x + 5)
        vid_clips.append(newclip)
        # print("vid_clips now has this many elements: " + str(len(vid_clips)))
        x = x + 5

    if x < vid.duration:
        newclip = vid.subclip(x, vid.duration - x)
        vid_clips.append(newclip)

    clips.append(vid_clips)

print("finished breaking up vid clips into 5 second chunks")

secondsDiviedBy5 = int(vids[0].audio.duration / 5)  # pyright: ignore
main_clip = clips[0]

people_vols = average_volumes[1:]
people_clips = clips[1:]

final_clips: List[VideoClip] = [main_clip[0]]

# going through every 5 seconds of the audio clips.
for i in range(1, secondsDiviedBy5):
    greater = True
    for x, xvol in enumerate(people_vols):
        greater = True
        for y, yvol in enumerate(people_vols):
            if y == x:
                continue
            if xvol[i] * 0.1 < yvol[i]:
                greater = False
                break

        if greater:
            print("interval " + str(i) + " had person " + str(x) + " greater vol")
            final_clips.append(people_clips[x][i])
            # final = concatenate_videoclips([final, people_clips[x][i]])
            break

    if not greater:
        print("interval " + str(i) + " had no greater person vol")
        final_clips.append(main_clip[i])
        # final = concatenate_videoclips([final, main_clip[i]])

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
