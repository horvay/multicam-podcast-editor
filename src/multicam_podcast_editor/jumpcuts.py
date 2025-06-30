import subprocess
import re
import os
import shutil


def apply_jumpcuts(vids: list[str], margin: float, output_name: str):
    silence_threshold: str = "-30dB"
    silence_duration: float = margin
    padding: float = margin / 2

    for i, vid in enumerate(vids):
        base_name = os.path.basename(vid)
        _, ext = os.path.splitext(base_name)

        is_short = "-short" in base_name
        if is_short:
            output_path = f"output/{output_name}-short-jumpcut{ext}"
        else:
            output_path = f"output/{output_name}-jumpcut{ext}"

        detect_command = [
            "ffmpeg",
            "-i",
            vid,
            "-af",
            f"silencedetect=n={silence_threshold}:d={silence_duration}",
            "-f",
            "null",
            "-",
        ]

        try:
            output = subprocess.run(
                detect_command,
                check=True,
                capture_output=True,
                text=True,
            ).stderr
        except subprocess.CalledProcessError as e:
            print(f"Error detecting silence: {e.stderr}")
            continue

        silence_starts = re.findall(r"silence_start: (-?\d+\.?\d*)", output)
        silence_ends = re.findall(r"silence_end: (-?\d+\.?\d*)", output)

        if not silence_starts:
            print("No silence detected, copying file.")
            shutil.copy(vid, output_path)
            continue

        chunks_to_cut = []
        for start, end in zip(silence_starts, silence_ends):
            start, end = float(start), float(end)
            if end - start >= 2 * padding:
                chunks_to_cut.append((start + padding, end - padding))

        if not chunks_to_cut:
            print("No silences long enough to cut after padding, copying file.")
            shutil.copy(vid, output_path)
            continue

        clips_to_keep = []
        last_end = 0.0
        for start, end in sorted(chunks_to_cut):
            clips_to_keep.append(f"between(t,{last_end},{start})")
            last_end = end

        clips_to_keep.append(f"gte(t,{last_end})")
        select_filter = "+".join(clips_to_keep)

        process_command = [
            "ffmpeg",
            "-y",
            "-i",
            vid,
            "-vf",
            f"select='{select_filter}',setpts=N/FRAME_RATE/TB",
            "-af",
            f"aselect='{select_filter}',asetpts=N/SR/TB",
            output_path,
        ]

        try:
            subprocess.run(process_command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f"Error removing silence: {e.stderr}")
            continue
