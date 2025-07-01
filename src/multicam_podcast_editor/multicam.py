import math
import re
import subprocess
from pathlib import Path
from typing import List, Tuple
from os import PathLike

from moviepy import VideoClip  # only used for durations/metadata – no heavy rendering


def _parse_screenshare_times(screenshares: List[str]) -> List[Tuple[float, float]]:
    """Extract start- and end-times for screen-share clips from their filenames.

    The expected filename format contains a timestamp such as
    "00h_01m_30s_500ms" which will be parsed into seconds.
    """

    reduced_focus_times: list[tuple[float, float]] = []

    for ss in screenshares:
        time_match = re.search(r"(\d+h_)?(\d+m_)?(\d+s_)?(\d+ms)", ss)

        if not time_match:
            print(f"[multicam] Time format not found in the screen file {ss}")
            continue

        hours = int(time_match.group(1)[:-2] if time_match.group(1) else 0)
        minutes = int(time_match.group(2)[:-2] if time_match.group(2) else 0)
        seconds = int(time_match.group(3)[:-2] if time_match.group(3) else 0)
        milliseconds = int(time_match.group(4)[:-2] if time_match.group(4) else 0)

        start_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000

        # We need the duration of the screen-share clip to know when to stop
        # de-focusing. We query ffprobe instead of loading with MoviePy.
        try:
            import json, shlex

            cmd = shlex.split(
                f"ffprobe -v error -select_streams v:0 -show_entries stream=duration -of json '{ss}'"
            )
            probe = subprocess.check_output(cmd, text=True)
            duration = float(json.loads(probe)["streams"][0]["duration"])
        except Exception:
            duration = 0.0

        end_seconds = start_seconds + duration
        reduced_focus_times.append((start_seconds, end_seconds))

        print(
            f"[multicam] creating less focused session from: {start_seconds:.2f}s to: {end_seconds:.2f}s"
        )

    return reduced_focus_times


def _safe_mkdir(path: "Path | str | PathLike") -> None:
    """Create directory recursively without throwing if it already exists."""
    Path(path).mkdir(parents=True, exist_ok=True)


def multicam(
    screenshares: List[str],
    video_paths: List[str],
    vids: List[VideoClip],
    average_volumes,
    paddings: List[float],
    threads: int = 10,
    output_name: str = "final",
):
    """Create a multi-cam cut using ffmpeg for speed.

    Parameters
    ----------
    screenshares
        List of screen-share clip paths whose time range should *de-focus* the
        speakers (i.e. force main camera).
    video_paths
        File-paths (on disk) matching the order of `vids` / `average_volumes`.
    vids
        MoviePy clips (only used for metadata such as duration – no rendering).
    average_volumes
        5-second window max-volume buckets calculated in :pyfunc:`analyze`.
    paddings
        The audio-sync padding (in seconds) applied to each video. ``paddings[0]``
        will always be ``0`` for the main video.
    """

    print("[multicam] Using ffmpeg backend ✅")

    ###########################################################################
    # Build the decision timeline – which camera should be shown each 5 secs. #
    ###########################################################################

    reduced_focus_times = _parse_screenshare_times(screenshares)

    seconds_divided_by_5: int = math.ceil(vids[0].audio.duration / 5)  # pyright: ignore
    main_clip = vids[0]

    people_vols = average_volumes[1:]
    people = vids[1:]

    # When a person's video ends before the main video, avoid showing a frozen
    # last frame.
    mandatory_unfocus: list[tuple[float, float]] = []
    for person in people:
        if person.duration < main_clip.duration:
            mandatory_unfocus.append((person.duration - 5, person.duration + 5))

    # Timeline decision data-structure: list of (video_index, local_start, duration)
    final_segments: List[Tuple[int, float, float]] = []

    unfocused_count = 0
    focused_count = 0

    # Helper for adding a segment with the correct (possibly trimmed) duration.
    def _add_segment(idx: int, start_time: float, end_time: float):
        duration = end_time - start_time
        if duration <= 0:
            return
        final_segments.append((idx, start_time, duration))

    # First 5-second chunk is always the main.
    _add_segment(0, 0, 5)

    for i in range(1, seconds_divided_by_5):
        sec = i * 5
        n_sec = sec + 5

        # Person stopped recording – fallback to main.
        if any(start < sec < end for start, end in mandatory_unfocus):
            _add_segment(0, sec, n_sec)
            continue

        # Closing seconds of the main video – keep it on-screen.
        if sec > main_clip.duration - 11:
            _add_segment(0, sec, n_sec)
            continue

        # If we are currently in a screenshare window & haven't been unfocused
        # for >10 seconds, keep main.
        if unfocused_count < 2 and any(start < sec < end for start, end in reduced_focus_times):
            _add_segment(0, sec, n_sec)
            unfocused_count, focused_count = unfocused_count + 1, 0
            continue

        # Look at who is loudest in this 5 second bucket.
        if focused_count < 2:
            current_iter_vols = [xvol[i] if len(xvol) > i else -100 for xvol in people_vols]
            sorted_vols = sorted(enumerate(current_iter_vols), key=lambda x: x[1], reverse=True)

            first = sorted_vols[0]
            second = sorted_vols[1] if len(sorted_vols) > 1 else None

            if second is None or first[1] * 0.05 > second[1]:
                # Person `first[0]` (plus 1 because `people` excludes main) wins.
                _add_segment(first[0] + 1, sec, n_sec)
                unfocused_count, focused_count = 0, focused_count + 1
                continue

        # Default to main.
        _add_segment(0, sec, n_sec)
        unfocused_count, focused_count = unfocused_count + 1, 0

    ###########################################################################
    # Merge consecutive segments from the same source to avoid excess cuts.   #
    ###########################################################################

    if len(final_segments) > 1:
        merged_segments: List[Tuple[int, float, float]] = []
        cur_idx, cur_start, cur_dur = final_segments[0]

        for next_idx, next_start, next_dur in final_segments[1:]:
            # If the next segment is from the same source and directly follows
            # the current one, extend the duration instead of creating a cut.
            if (
                next_idx == cur_idx
                and abs((cur_start + cur_dur) - next_start) < 1e-3  # contiguous
            ):
                cur_dur += next_dur
            else:
                merged_segments.append((cur_idx, cur_start, cur_dur))
                cur_idx, cur_start, cur_dur = next_idx, next_start, next_dur

        merged_segments.append((cur_idx, cur_start, cur_dur))
        final_segments = merged_segments

    ###########################################################################
    # Render video with ffmpeg                                                    #
    ###########################################################################

    segment_dir = Path("temp/segments")
    _safe_mkdir(segment_dir)

    concat_file = segment_dir / "list.txt"
    with concat_file.open("w") as f_list:
        for seg_idx, (vid_idx, local_start, duration) in enumerate(final_segments):
            # Map local timeline to original file timeline.
            if vid_idx == 0:
                src_start = local_start + 5  # main video had first 5 s removed.
            else:
                offset = 5 - paddings[vid_idx]
                src_start = local_start + offset

                # If the calculated start would be before 0, we fallback to main
                # camera for safety.
                if src_start < 0:
                    vid_idx = 0
                    src_start = local_start + 5

            src_path = video_paths[vid_idx]

            out_file = segment_dir / f"seg_{seg_idx:04d}.mp4"

            # Build ffmpeg command for the individual segment.  We *re-encode*
            # with an ultrafast preset instead of stream-copy so the first
            # frame becomes a clean keyframe.  This prevents visual glitches
            # (black/green flicker) when switching between cameras that use
            # different GOP alignment.
            cmd_extract = (
                f"ffmpeg -loglevel error -threads {threads} -ss {src_start} -t {duration} "
                f"-i '{src_path}' -c:v libx264 -preset ultrafast -crf 18 -pix_fmt yuv420p "
                f"-g 15 -keyint_min 15 -sc_threshold 0 -an -y '{out_file}'"
            )
            print(f"[multicam] extracting segment {seg_idx}: {cmd_extract}")
            subprocess.run(cmd_extract, shell=True, check=True)

            f_list.write(f"file '{out_file.resolve()}'\n")

    combined_video = segment_dir / "combined_video.mp4"
    cmd_concat = f"ffmpeg -loglevel error -threads {threads} -f concat -safe 0 -i '{concat_file}' -c copy -y '{combined_video}'"
    print(f"[multicam] concatenating segments: {cmd_concat}")
    subprocess.run(cmd_concat, shell=True, check=True)

    ###########################################################################
    # Mix audio (persons only)                                                  #
    ###########################################################################

    if len(video_paths) > 1:
        audio_mix = segment_dir / "audio_mix.m4a"

        # Build inputs for ffmpeg command.
        person_inputs = " ".join(f"-i '{p}'" for p in video_paths[1:])

        delay_filters = []
        delayed_labels = []
        for idx, pad in enumerate(paddings[1:], start=0):
            delay_ms = max(0, (pad - 5)) * 1000  # align to the 5-second trimming
            label_out = f"a{idx}"
            delay_filters.append(f"[{idx}:a]adelay={int(delay_ms)}|{int(delay_ms)}[{label_out}]")
            delayed_labels.append(f"[{label_out}]")

        filter_complex = ";".join(delay_filters + [
            "".join(delayed_labels) + f"amix=inputs={len(delayed_labels)}:duration=longest[aout]"
        ])

        cmd_audio = (
            f"ffmpeg -loglevel error {person_inputs} -filter_complex \"{filter_complex}\" "
            f"-map '[aout]' -c:a aac -b:a 256k -y '{audio_mix}'"
        )
        print(f"[multicam] mixing audio: {cmd_audio}")
        subprocess.run(cmd_audio, shell=True, check=True)
    else:
        audio_mix = None

    ###########################################################################
    # Combine video & audio                                                     #
    ###########################################################################

    output_path = Path("output") / f"{output_name}.mp4"
    _safe_mkdir(output_path.parent)

    if audio_mix and audio_mix.exists():
        cmd_mux = (
            f"ffmpeg -loglevel error -i '{combined_video}' -i '{audio_mix}' -map 0:v:0 -map 1:a:0 "
            f"-c:v copy -c:a aac -shortest -y '{output_path}'"
        )
    else:
        # Fallback: use the video with its original (segment) audio – unlikely
        # to be desired, but avoids total failure.
        cmd_mux = f"ffmpeg -loglevel error -i '{combined_video}' -c copy -y '{output_path}'"

    print(f"[multicam] muxing final video: {cmd_mux}")
    subprocess.run(cmd_mux, shell=True, check=True)

    print(f"[multicam] ✅ finished – output at {output_path}")
