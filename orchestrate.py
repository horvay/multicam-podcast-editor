import os
import random
import subprocess
import shutil

from analyze_video import analyze
from args_parser import Args
from audio_enhancement import podcast_audio
from captioning import caption_video, transcribe_file
from chat import chat_with_transcript
from collage import create_music_video, populate_file_with_images
from jumpcuts import apply_jumpcuts
from multicam import multicam
from short_creator import shortcut
from transcribe import transcribe


def _clear_temp_folder():
    if os.path.exists("temp"):
        for filename in os.listdir("temp"):
            file_path = os.path.join("temp", filename)
            os.unlink(file_path)  # unlink also deletes


def run(options: Args):
    if options.output_name == "final":
        options.output_name = f"final{int(random.random()*10000)}"

    _clear_temp_folder()

    os.makedirs("temp", exist_ok=True)
    os.makedirs("output", exist_ok=True)

    def _copy_to_temp(file: str):
        new_file = "temp/" + os.path.basename(file)
        shutil.copy(file, new_file)
        return new_file

    assert (options.collage_dir is None and options.collage_input is None) or (
        options.collage_dir is not None and options.collage_input is not None
    ), "collage-dir and collage-input must be used together"

    if options.collage_input is not None and options.collage_dir is not None:
        assert os.path.exists(options.collage_input), "collage-input does not exist"
        assert os.path.exists(options.collage_dir), "collage-dir does not exist"
        populate_file_with_images(options.collage_input, options.collage_dir)

    if options.multicam or options.short is not None:
        new_file = _copy_to_temp(options.multicam_main_vid)
        options.multicam_main_vid = new_file

        for i, vid in enumerate(options.multicam_input):
            new_file = _copy_to_temp(vid)
            options.multicam_input[i] = new_file

    ##################################################

    all_people = [options.multicam_main_vid] + options.multicam_input

    if options.short is not None:
        max_time = options.till or options.short + 180
        print(f"trimming until time {max_time+10}s")
        for vid in all_people:
            fp_vid = os.path.abspath(vid)
            command = f"ffmpeg -i '{fp_vid}' -t {max_time + 10} -c copy temp/output.mp4"
            subprocess.run(command, shell=True)
            shutil.move("temp/output.mp4", fp_vid)

    print(all_people)

    average_volumes = []
    vids = []

    if options.multicam or options.short is not None:
        max_time = -1
        if options.short is not None:
            max_time = options.till or options.short + 180

        vids, average_volumes = analyze(
            all_people,
            max_time,
            options.align_videos,
            options.skip_bitrate_sync,
            options.threads,
        )

    if options.multicam:
        multicam(
            options.screenshare_input,
            vids,
            average_volumes,
            options.threads,
            options.output_name,
        )

    if options.short is not None:
        shortcut(
            vids,
            average_volumes,
            options.short,
            options.till,
            options.cut,
            options.threads,
            options.output_name,
        )

    print(f"apply jumpcuts? {options.jump_cuts}")
    if options.jump_cuts:
        vids_to_jumpcut: list[str] = []
        if os.path.exists(f"output/{options.output_name}.mp4"):
            vids_to_jumpcut.append(f"output/{options.output_name}.mp4")

        if os.path.exists(f"output/{options.output_name}-short.mp4"):
            vids_to_jumpcut.append(f"output/{options.output_name}-short.mp4")

        apply_jumpcuts(
            vids_to_jumpcut,
            options.jump_cuts_margin,
            options.hi_def,
            options.output_name,
        )

    if options.audio_enhancements:
        vids_to_enhance: list[str] = []
        if os.path.exists(f"output/{options.output_name}.mp4"):
            vids_to_enhance.append(f"output/{options.output_name}.mp4")

        if os.path.exists(f"output/{options.output_name}-short.mp4"):
            vids_to_enhance.append(f"output/{options.output_name}-short.mp4")

        if os.path.exists(f"output/{options.output_name}-jumpcut.mp4"):
            vids_to_enhance.append(f"output/{options.output_name}-jumpcut.mp4")

        if os.path.exists(f"output/{options.output_name}-short-jumpcut.mp4"):
            vids_to_enhance.append(f"output/{options.output_name}-short-jumpcut.mp4")

        podcast_audio(vids_to_enhance, options.threads)

    if options.transcribe:
        transcribe(options.multicam_input, options.word_pause)

    if options.transcribe_file is not None and options.transcribe_file != "":
        transcribe_file(options.transcribe_file)

    if options.caption_video is not None and options.caption_video != "":
        if options.caption_csv is None or options.caption_csv == "":
            options.caption_csv = f"{options.caption_video}.csv"

        caption_video(
            options.caption_video,
            options.caption_csv,
            options.font,
            options.font_size,
            options.caption_position,
            options.caption_size,
            options.caption_type,
        )

    if options.question != "" and options.question is not None:
        chat_with_transcript(options.question, options.model)

    if options.music_video_music is not None and options.music_video_art is not None:
        create_music_video(
            options.music_video_music,
            options.music_video_art,
            options.music_video_reminders,
        )
