import os
from tprint import print_decorator
from ffmpeg_normalize import FFmpegNormalize

print = print_decorator(print)


def podcast_audio(vid_list, threads=10):
    print("list of vids found to process" + str(vid_list))

    if os.path.exists("temp_video.mp4"):
        os.remove("temp_video.mp4")

    for vid in vid_list:
        normalize = FFmpegNormalize(
            target_level=-14,
            true_peak=-1.0,
            progress=True,
            audio_codec="aac",
            output_format="mp4",
            pre_filter="deesser,firequalizer=gain_entry='entry(100,0);entry(125,-2);entry(160,-6);entry(200,6);entry(250,-7);entry(315,3);entry(400,-8);entry(500,-4);entry(630,-2);entry(700,-11);entry(800,-6);entry(1000,-4);entry(1250,-14);entry(1600,-11);entry(2000,3);entry(2500,-10);entry(3150,-1);entry(3500,-12);entry(4000,-1);entry(5000,-6);entry(6300,-10);entry(8000,-10);entry(10000,-15);entry(12500,-20);entry(16000,-20)',acompressor=threshold=-12dB:ratio=3:attack=10:release=100,loudnorm=I=-14:LRA=7:TP=-1",
            extra_input_options=[
                "-threads",
                f"{threads}",
                "-filter_threads",
                f"{threads}",
                "-filter_complex_threads",
                f"{threads}",
            ],
        )
        normalize.add_media_file(vid, vid)
        normalize.run_normalization()
