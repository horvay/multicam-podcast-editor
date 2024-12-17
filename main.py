import argparse
import glob
import os
from typing import List

from analyze_video import analyze
from audio_enhancement import podcast_audio
from captioning import caption_video, transcribe_file
from chat import chat_with_transcript
from multicam import multicam
from short_creator import shortcut
from tprint import print_decorator
from transcribe import transcribe

print = print_decorator(print)


def parse_time_pairs(arg_strings: List[str]):
    times = []
    for pair in arg_strings:
        try:
            start = 0.0
            stop = 0.0
            start, stop = map(float, pair.split(","))
            if stop <= start:
                raise ValueError("Stop time must be greater than start time")
            times.append((start, stop))
        except ValueError as e:
            raise argparse.ArgumentTypeError(
                f"Invalid time pair format. {e} - on pair |{pair}| in {arg_strings}"
            )
    return times


# Add an argument that can take multiple pairs of floats

parser = argparse.ArgumentParser(
    description="A cli to automatically multicam edit, jump cut, transcribe and interact with your podcast with an LLM"
)

parser.add_argument(
    "-m", "--multicam", action="store_true", help="do automatic multicam edits"
)
parser.add_argument(
    "-j", "--jump-cuts", action="store_true", help="do automatic jump cuts of dead air"
)
parser.add_argument(
    "-au",
    "--audio-podcast-enhancements",
    action="store_true",
    help="enhance the audio using some standard podcast audio filters",
)
parser.add_argument(
    "-t",
    "--transcribe",
    action="store_true",
    help="transcribe the podcast to a text file",
)
parser.add_argument(
    "-sb",
    "--skip-bitrate-sync",
    action="store_true",
    help="by default the audio bitrates of each file will be made the same",
)
parser.add_argument(
    "-nt",
    "--threads",
    type=int,
    help="the amount of threads to use for certain task when generating video or audio. Defaults to 10",
    default=10,
)
parser.add_argument(
    "-s",
    "--short",
    type=int,
    help="Create a short starting at this second for 1 minute or until --till is set. Ex: --short 127 --till 148 (ie, create a 21 second short starting at 127 seconds in until 148s)",
)
parser.add_argument(
    "-ti",
    "--till",
    type=int,
    help="When to stop generating the short. If not set, then a short will default to 1 minute. Ex: --short 127 --till 148 (ie, create a 21 second short starting at 127 seconds in until 148s)",
)
parser.add_argument(
    "-c",
    "--cut",
    type=float,
    nargs=2,
    action="append",
    help="Pairs of start and stop times in seconds to skip. Example: -c 1.0 2.0 -c 3.0 4.0",
)
parser.add_argument(
    "-w",
    "--word-pause",
    type=float,
    help="The length of time between words to detect a new line in the transcript. Defaults to 1.2",
    default=1.2,
)
parser.add_argument(
    "-is",
    "--ignore-screenshares",
    action="store_true",
    help="by default when the screen is shared more emphasis will be put on the group video with the scerenshare. Requires putting the screenshare files in the same directory",
)
parser.add_argument(
    "-a",
    "--align-videos",
    action="store_true",
    help="align videos based on volumes",
    default=True,
)
parser.add_argument(
    "-hd",
    "--hi-def",
    action="store_true",
    help="set the output to 1080p. Defaults to true",
    default=True,
)
parser.add_argument(
    "-q",
    "--question",
    type=str,
    help="ask your transcript a question with an OLLAMA",
    default="",
)
parser.add_argument(
    "-o",
    "--output-name",
    type=str,
    help="The name of the file to generate in the output folder",
    default="final",
)
parser.add_argument(
    "-mo",
    "--model",
    type=str,
    help="when asking a question, which model should be used? Defaults to llama3.2-vision",
    default="llama3.2-vision",
)
parser.add_argument(
    "-tf",
    "--transcribe-file",
    metavar="file",
    type=str,
    help="transcribe a single file word by word usually to be used for generating lyrics on a video",
    default="",
)
parser.add_argument(
    "-cv",
    "--caption-video",
    type=str,
    metavar="video",
    help="the video to caption and csv with the same name as the video, so 'inputfiles/myvideo.mp4' would need inputfiles/myvideo.mp4.csv to exist. Use -tf to generate the csv",
    default="",
)


args = parser.parse_args()

print(args)

individuals = glob.glob("inputfiles/person*.mp4") + glob.glob("inputfiles/*webcam*.mp4")
screenshares = glob.glob("inputfiles/*screen*.mp4")
all_people = ["inputfiles/main.mp4"] + individuals
print(all_people)


average_volumes = []
vids = []

outputname = args.output_name or "final"

os.makedirs("temp", exist_ok=True)

if args.multicam or args.short is not None:
    vids, average_volumes = analyze(
        all_people, args.align_videos, args.skip_bitrate_sync, args.threads
    )

if args.multicam:
    multicam(
        screenshares,
        args.jump_cuts,
        vids,
        average_volumes,
        args.hi_def,
        args.threads,
        args.output_name,
    )

if args.short is not None:
    shortcut(
        vids,
        average_volumes,
        args.short,
        args.till,
        args.cut,
        args.jump_cuts,
        args.threads,
        args.output_name,
    )

# podcast_audio(["inputfiles/main2.mp4"], args.threads)

if args.audio_podcast_enhancements:
    vids_to_enhance: list[str] = []
    if os.path.exists(f"output/{args.output_name}.mp4"):
        vids_to_enhance.append(f"output/{args.output_name}.mp4")

    if os.path.exists(f"output/{args.output_name}-short.mp4"):
        vids_to_enhance.append(f"output/{args.output_name}-short.mp4")

    if os.path.exists(f"output/{args.output_name}-jumpcut.mp4"):
        vids_to_enhance.append(f"output/{args.output_name}-jumpcut.mp4")

    if os.path.exists(f"output/{args.output_name}-short-jumpcut.mp4"):
        vids_to_enhance.append(f"output/{args.output_name}-short-jumpcut.mp4")

    podcast_audio(vids_to_enhance, args.threads)


if args.transcribe:
    transcribe(individuals, args.word_pause)

if args.transcribe_file != "":
    transcribe_file(args.transcribe_file)

if args.caption_video != "":
    caption_video(args.caption_video)

if args.question != "":
    chat_with_transcript(args.question, args.model)
