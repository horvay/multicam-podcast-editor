import glob
import argparse

from chat import chat_with_transcript
from multicam import multicam
from transcribe import transcribe

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
    "-t",
    "--transcribe",
    action="store_true",
    help="transcribe the podcast to a text file",
)
parser.add_argument(
    "-w",
    "--word-pause",
    type=float,
    help="The length of time between words to detect a new line in the transcript. Defaults to 1.0",
    default=1.0,
)
parser.add_argument(
    "-s",
    "--screenshares",
    metavar="true",
    type=bool,
    help="if set it will focus less on individuals during screen shares, default to true",
    default=True,
)
parser.add_argument(
    "-a",
    "--align-videos",
    type=bool,
    metavar="true",
    help="align videos based on volumes",
    default=True,
)
parser.add_argument(
    "-hd",
    "--hi-def",
    type=bool,
    metavar="true",
    help="if using the auto jump cuts, set the output to 1080p. Defaults to true",
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
    "-mo",
    "--model",
    type=str,
    help="when asking a question, which model should be used? Defaults to llama3.2-vision",
    default="llama3.2-vision",
)


args = parser.parse_args()

individuals = glob.glob("person*.mp4") + glob.glob("*webcam*.mp4")
screenshares = glob.glob("*screen*.mp4")
all_people = ["main.mp4"] + individuals

if args.multicam:
    multicam(all_people, screenshares, args.jump_cuts, args.hi_def)

if args.transcribe:
    transcribe(individuals, args.word_pause)

if args.question != "":
    chat_with_transcript(args.question, args.model)
