import os
from tprint import print_decorator
from ffmpeg_normalize import FFmpegNormalize

print = print_decorator(print)


def podcast_audio(vid_list, enhance_type, threads=10):
    print("list of vids found to process" + str(vid_list))

    if os.path.exists("temp_video.mp4"):
        os.remove("temp_video.mp4")

    filters = (
        "afftdn=nr=12:nf=-50, anequalizer='c0 f=100 w=100 g=3 t=0, c0 f=10000 w=2000 g=3 t=0, c1 f=100 w=100 g=3 t=0, c1 f=10000 w=2000 g=3 t=0', acompressor"
        if enhance_type == "music"
        else "afftdn=nr=12:nf=-50, acompressor"
    )

    for vid in vid_list:
        normalize = FFmpegNormalize(
            target_level=-14,
            true_peak=-1.0,
            progress=True,
            audio_codec="aac",
            output_format="mp4",
            pre_filter=filters,
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
