from typing import List, Tuple
import subprocess
import os
import tempfile
from multicam_podcast_editor.tprint import print_decorator

print = print_decorator(print)


def cut_video(
    vid: str,
    cuts: List[Tuple[float, float]],
    threads: int = 10,
    output_name: str = "final",
):
    """
    Cut specified segments from a video and concatenate the remaining parts using FFmpeg.

    Args:
        vid (str): Path to the input video file.
        cuts (List[Tuple[float, float]]): List of (start, end) times in seconds to cut out.
        threads (int): Number of threads for video processing.
        output_name (str): Base name for the output file.
    """
    print(f"Cutting video {vid} with cuts: {cuts}")

    # Get video duration using FFmpeg
    ffprobe_cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        vid,
    ]
    duration = float(subprocess.check_output(ffprobe_cmd).decode().strip())

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

    # Create temporary directory for intermediate files
    with tempfile.TemporaryDirectory() as tmpdirname:
        temp_files = []
        # Process each playable segment
        for i, (start, end) in enumerate(play_segments):
            temp_output = os.path.join(tmpdirname, f"segment_{i}.mp4")
            duration = end - start
            ffmpeg_cmd = [
                "ffmpeg",
                "-y",
                "-i",
                vid,
                "-ss",
                str(start),
                "-t",
                str(duration),
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
                "-preset",
                "slow",
                "-b:v",
                "3000k",
                "-threads",
                str(threads),
                "-avoid_negative_ts",
                "make_zero",
                temp_output,
            ]
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
            temp_files.append(temp_output)

        # Create file list for concatenation
        concat_list_path = os.path.join(tmpdirname, "concat_list.txt")
        with open(concat_list_path, "w") as f:
            for temp_file in temp_files:
                f.write(f"file '{temp_file}'\n")

        # Concatenate segments
        output_path = f"output/{output_name}.mp4"
        os.makedirs("output", exist_ok=True)
        concat_cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",  # Allow unsafe file paths
            "-i",
            concat_list_path,
            "-c",
            "copy",  # Copy streams without re-encoding
            "-threads",
            str(threads),
            output_path,
        ]
        subprocess.run(concat_cmd, check=True, capture_output=True)

    print(f"Video saved to {output_path}")
    return output_path
