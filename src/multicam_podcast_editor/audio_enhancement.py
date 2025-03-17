import os
import logging
from shutil import move
import subprocess

import torch
from multicam_podcast_editor.tprint import print_decorator
from ffmpeg_normalize import FFmpegNormalize
from demucs import pretrained, apply
import torchaudio

logging.basicConfig(level=logging.WARNING)
logging.getLogger("ffmpeg_normalize").setLevel(logging.WARNING)

print = print_decorator(print)


def podcast_audio(vid_list, enhance_type, threads=10):
    print("list of vids found to process" + str(vid_list))

    if os.path.exists("temp_video.mp4"):
        os.remove("temp_video.mp4")

    if enhance_type == "music":
        filters = (
            "afftdn=nr=12:nf=-50, anequalizer='c0 f=200 w=200 g=1.5 t=0, c0 f=7000 w=2000 g=2 t=0, c1 f=200 w=200 g=1.5 t=0, c1 f=7000 w=2000 g=2 t=0', "
            "acompressor=threshold=-18dB:ratio=3:1:attack=5:release=50 "
        )
    else:
        filters = (
            "afftdn, "
            "adeclick, "
            "adeclip=window=40:threshold=5:hsize=200, "
            "highpass=f=30, "
            "loudnorm=I=-14:TP=-3:LRA=7, "
            "alimiter=level_in=1:level_out=1:limit=-1dB:attack=5:release=50:asc=true:asc_level=0.8"
        )

    for vid in vid_list:
        if enhance_type == "podcast":
            subprocess.run(
                f"ffmpeg -i {vid} -vn -acodec pcm_s16le -ar 48000 temp/temp-audio.wav -y",
                shell=True,
            )
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            waveform, sample_rate = torchaudio.load("./temp/temp-audio.wav")
            print(f"Input waveform shape: {waveform.shape}")

            model = pretrained.get_model("htdemucs_ft").to(device)
            waveform = waveform.to(device)
            model.eval()

            with torch.no_grad():
                denoised_waveform = apply.apply_model(model, waveform.unsqueeze(0))[
                    0
                ].cpu()
            denoised_waveform = denoised_waveform[3]
            print(f"Denoised waveform shape: {denoised_waveform.shape}")

            torchaudio.save(
                "./temp/temp-enhanced-audio.wav", denoised_waveform, sample_rate
            )

            subprocess.run(
                f"ffmpeg -i temp/temp-enhanced-audio.wav -af '{filters}'  temp/temp-enhanced-audio2.wav -y",
                shell=True,
            )

            subprocess.run(
                f"ffmpeg -i {vid} -i temp/temp-enhanced-audio2.wav -c:v copy -map 0:v:0 -map 1:a:0 temp/output.mp4 -y",
                shell=True,
            )

            move(os.path.abspath("temp/output.mp4"), vid)
