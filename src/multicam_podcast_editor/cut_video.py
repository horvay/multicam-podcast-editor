from typing import List, Tuple
from moviepy import VideoFileClip, concatenate_videoclips
from multicam_podcast_editor.tprint import print_decorator

print = print_decorator(print)


def cut_video(
    vid: str,
    cuts: List[Tuple[float, float]],
    threads: int = 10,
    output_name: str = "final",
):
    """
    Cut specified segments from a video and concatenate the remaining parts.

    Args:
        vid (str): Path to the input video file.
        cuts (List[Tuple[float, float]]): List of (start, end) times in seconds to cut out.
        threads (int): Number of threads for video processing.
        output_name (str): Base name for the output file.
    """
    print(f"Cutting video {vid} with cuts: {cuts}")

    # Load the video
    video = VideoFileClip(vid)
    duration = video.duration

    # Sort cuts by start time and calculate playable segments
    sorted_cuts = sorted(cuts, key=lambda x: x[0])
    play_segments = []
    start = 0
    for cut_start, cut_end in sorted_cuts:
        if start < cut_start:
            play_segments.append((start, cut_start))
        start = cut_end
    if start < duration:
        play_segments.append((start, duration))

    print(f"Playable segments: {play_segments}")

    # Create subclips for each playable segment
    clips = [video.subclipped(s, e) for s, e in play_segments]

    # Concatenate the clips
    final_video = concatenate_videoclips(clips)

    # Write the output file using output_name directly
    output_path = f"output/{output_name}.mp4"
    final_video.write_videofile(
        output_path,
        threads=threads,
        codec="libx264",
        audio_codec="aac",
        preset="slow",
        bitrate="3000k",
    )

    print(f"Video saved to {output_path}")
    return output_path
