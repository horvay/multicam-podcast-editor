import os
import subprocess
from tprint import print_decorator
from ffmpeg_normalize import FFmpegNormalize

print = print_decorator(print)
filters = "highpass=f=50, lowpass=f=10000, adeclick, firequalizer=gain_entry='entry(100,0); entry(125,-1); entry(160,-2); entry(200,2); entry(250,-2); entry(315,1); entry(400,-2); entry(500,-1); entry(630,-1); entry(700,-3); entry(800,-2); entry(1000,-1); entry(1250,-2); entry(1600,-2); entry(2000,0); entry(2500,-2); entry(3150,0); entry(3500,-2); entry(4000,0); entry(5000,-1); entry(6300,-2); entry(8000,-2); entry(10000,-2); entry(12500,-3); entry(16000,-3)', alimiter=limit=-1dB:attack=0.012dB:release=0.2dB, asendcmd=0 afftdn sn start, asendcmd=1 afftdn sn stop, afftdn=nr=20:nf=-55, deesser"


def podcast_audio(vid_list, threads=10):
    print("list of vids found to process" + str(vid_list))

    if os.path.exists("temp_video.mp4"):
        os.remove("temp_video.mp4")

    for vid in vid_list:
        command = f"ffmpeg -threads {threads} -i '{vid}' -map 0:v -map 0:a -c:v copy -af \"{filters}\" temp_video.mp4 && cp temp_video.mp4 '{vid}'"
        subprocess.run(command, shell=True)
        os.remove("temp_video.mp4")
        normalize = FFmpegNormalize(
            target_level=-14,  # Target Loudness -18 LUFS
            true_peak=-1.0,  # Max True Peak Level -1 dBTP
            progress=True,  # Set to True if you want to see progress
            audio_codec="aac",  # Choose your preferred codec
            output_format="mp4",  # Choose your preferred format
            # extra_output_options=[
            #     "-af",
            #     "alimiter=limit=-1:attack=0.012:release=0.2",  # True Peak Limiting with look ahead and release time
            # ],
        )
        normalize.add_media_file(vid, vid)
        normalize.run_normalization()
