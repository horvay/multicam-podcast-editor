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
            # pre_filter="deesser,firequalizer=gain_entry='entry(100,0);entry(125,-1);entry(160,-3);entry(200,3);entry(250,-4);entry(315,2);entry(400,-4);entry(500,-2);entry(630,-1);entry(700,-6);entry(800,-3);entry(1000,-2);entry(1250,-7);entry(1600,-6);entry(2000,2);entry(2500,-5);entry(3150,0);entry(3500,-6);entry(4000,0);entry(5000,-3);entry(6300,-5);entry(8000,-5);entry(10000,-8);entry(12500,-10);entry(16000,-10)',acompressor=threshold=-12dB:ratio=3:attack=10:release=100,loudnorm=I=-14:LRA=7:TP=-1",
            pre_filter="deesser,firequalizer=gain_entry='entry(0,0); entry(100,0); entry(150,2); entry(300,0); entry(400,-2); entry(800,-1); entry(1000,-1); entry(7000,0)',acompressor=threshold=-12dB:ratio=3:attack=10:release=100,loudnorm=I=-14:LRA=7:TP=-1",
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
