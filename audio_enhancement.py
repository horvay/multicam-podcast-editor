import os
import subprocess
from tprint import print_decorator
from ffmpeg_normalize import FFmpegNormalize

print = print_decorator(print)
filters = "highpass=f=50, lowpass=f=15000, adeclick, firequalizer=gain_entry='entry(100,0); entry(125,-1); entry(160,-2); entry(200,2); entry(250,-2); entry(315,1); entry(400,-2); entry(500,-1); entry(630,-1); entry(700,-3); entry(800,-2); entry(1000,-1); entry(1250,-4); entry(1600,-3); entry(2000,0); entry(2500,-3); entry(3150,0); entry(3500,-3); entry(4000,0); entry(5000,-2); entry(6300,-3); entry(8000,-3); entry(10000,-3); entry(12500,-5); entry(16000,-5)', alimiter=level=false:limit=-3dB, asendcmd=0 afftdn sn start, asendcmd=1 afftdn sn stop, afftdn=nr=20:nf=-55, deesser"


def podcast_audio(vid_list, threads=10):
    print("list of vids found to process" + str(vid_list))

    if os.path.exists("temp_video.mp4"):
        os.remove("temp_video.mp4")

    for vid in vid_list:
        command = f"ffmpeg -threads {threads} -i '{vid}' -map 0:v -map 0:a -c:v copy -af \"{filters}\" temp_video.mp4 && cp temp_video.mp4 '{vid}'"
        subprocess.run(command, shell=True)
        os.remove("temp_video.mp4")
        normalize = FFmpegNormalize(progress=True, audio_codec="wav", target_level=-14)
        normalize.add_media_file(vid, vid)
