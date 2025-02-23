import os
import random
import subprocess
import shutil
import time

from multicam_podcast_editor.analyze_video import analyze
from multicam_podcast_editor.args_parser import Args
from multicam_podcast_editor.audio_enhancement import podcast_audio
from multicam_podcast_editor.captioning import caption_video, transcribe_file
from multicam_podcast_editor.collage import (
    create_music_video,
    populate_file_with_images,
)
from multicam_podcast_editor.jumpcuts import apply_jumpcuts
from multicam_podcast_editor.multicam import multicam
from multicam_podcast_editor.short_creator import shortcut
from multicam_podcast_editor.transcribe import transcribe


def _clear_temp_folder():
    if os.path.exists("temp"):
        for filename in os.listdir("temp"):
            file_path = os.path.join("temp", filename)
            os.unlink(file_path)  # unlink also deletes


def run(options: Args):
    if options.seed == -1:
        seed = int(time.time())
        random.seed(seed)
        print(f"using seed: {seed}. Use -se to get same generations")
    else:
        random.seed(options.seed)
        print(f"using provided seed of {options.seed}")

    if options.output_name == "final":
        options.output_name = f"final{int(random.random()*10000)}"

    _clear_temp_folder()

    os.makedirs("temp", exist_ok=True)
    os.makedirs("output", exist_ok=True)

    def _copy_to_temp(file: str):
        new_file = "temp/" + os.path.basename(file)
        shutil.copy(file, new_file)
        return new_file

    if options.collage:
        assert len(options.inputs) == 2, "must provide both movie and image directory"

        moviefile, art_dir = options.inputs
        assert os.path.exists(moviefile) and os.path.exists(art_dir), "invalid paths"

        populate_file_with_images(moviefile, art_dir, options.output_name)

    if options.multicam or options.short is not None:
        assert len(options.inputs) >= 2, "multicam must have 2 or more files"
        for vid_index, dir in enumerate(options.inputs):
            assert os.path.exists(dir), f"vid file {dir} not a valid file"
            temp_file = _copy_to_temp(dir)
            options.inputs[vid_index] = temp_file

    ##################################################

    if options.short is not None:
        max_time = options.till or options.short + 180
        print(f"trimming until time {max_time+10}s")

        assert (
            len(options.inputs) >= 2
        ), "creating short from multicam must have 2 or more files"
        for vid_index, dir in enumerate(options.inputs):
            assert os.path.exists(dir), f"vid file {dir} not a valid file"
            fp_vid = os.path.abspath(dir)
            command = f"ffmpeg -i '{fp_vid}' -t {max_time + 10} -c copy temp/output.mp4"
            subprocess.run(command, shell=True)
            shutil.move("temp/output.mp4", fp_vid)

    print(options.inputs)

    average_volumes = []
    vids = []

    if (
        options.multicam
        or options.short
        or (options.transcribe and len(options.inputs) >= 2)
    ):
        max_time = -1
        if options.short is not None:
            max_time = options.till or options.short + 180

        vids, average_volumes = analyze(
            options.inputs,
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

    if options.transcribe:
        if len(options.inputs) == 1:
            transcribe_file(options.inputs[0])
        elif len(options.inputs) >= 2:
            transcribe(options.inputs[1:], options.word_pause)

    if options.caption_video:
        if options.caption_csv is None or options.caption_csv == "":
            options.caption_csv = f"{options.caption_video}.csv"

        assert os.path.exists(
            options.caption_csv
        ), f"can't find lyric file {options.caption_csv}"

        assert len(options.inputs) > 0 and os.path.exists(
            options.inputs[0]
        ), "required valid input"

        caption_video(
            options.inputs[0],
            options.caption_csv,
            options.font,
            options.font_size,
            options.caption_position,
            options.caption_size,
            options.caption_type,
        )

    if options.music_video:
        assert (
            len(options.inputs) >= 2 and len(options.inputs) <= 3
        ), "music video should only have 2-3 inputs"

        if options.thumbnail != "":
            assert os.path.exists(
                options.thumbnail
            ), f"thumbnail doesn't exist at {options.thumbnail}"

        for dir in options.inputs:
            assert os.path.exists(dir), f"vid file {dir} not a valid file"

        music, art, *reminders = options.inputs
        reminders = None if reminders == [] else reminders[0]

        create_music_video(
            music, art, options.output_name, reminders, options.thumbnail
        )

    if options.audio_podcast_enhancements or options.audio_music_enhancements:
        vids_to_enhance: list[str] = []

        if os.path.exists(f"output/{options.output_name}.mp4"):
            vids_to_enhance.append(f"output/{options.output_name}.mp4")

        if os.path.exists(f"output/{options.output_name}-short.mp4"):
            vids_to_enhance.append(f"output/{options.output_name}-short.mp4")

        if os.path.exists(f"output/{options.output_name}-jumpcut.mp4"):
            vids_to_enhance.append(f"output/{options.output_name}-jumpcut.mp4")

        if os.path.exists(f"output/{options.output_name}-short-jumpcut.mp4"):
            vids_to_enhance.append(f"output/{options.output_name}-short-jumpcut.mp4")

        if len(vids_to_enhance) == 0 and len(options.inputs) == 1:
            input = options.inputs[0]
            ext = os.path.splitext(input)[1]

            assert os.path.exists(input), f"input {input} doesn't exist"
            newfile = f"output/{options.output_name}{ext}"
            shutil.copy(input, newfile)

            vids_to_enhance.append(newfile)

        enhance_type = "music" if options.audio_music_enhancements else "podcast"

        podcast_audio(vids_to_enhance, enhance_type, options.threads)
