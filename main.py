import argparse

from args_parser import parse_cli_args
from orchestrate import run
from tprint import print_decorator

print = print_decorator(print)


parser = argparse.ArgumentParser(
    description="A cli to automatically multicam edit, jump cut, transcribe and interact with your podcast with an LLM"
)
parser.add_argument(
    "-m", "--multicam", action="store_true", help="do automatic multicam edits"
)
parser.add_argument(
    "-mm",
    "--multicam-main-vid",
    type=str,
    metavar="video",
    help="name of the main baseline video to use for the automatic multicam",
    default="inputfiles/main.mp4",
)
parser.add_argument(
    "-mi",
    "--multicam-input",
    action="append",
    nargs="+",
    help="Used for adding individuals' videos in the multicam scenarios. Use -mm for the main video, and this for individual files. By default it looks for person*.mp4 or *webcam*.mp4 files. ex: -mi 'inputfiles/myperson1.mp4' -mi 'inputfiles/myperson2.mp4' etc",
)
parser.add_argument(
    "-si",
    "--screenshare-input",
    action="append",
    nargs="+",
    help="Used for adding screenshare videos used in the multicam scenarios. Use -mm for the main video, and this for screenshare files. By default it looks for *screenshare*.mp4 or *webcam*.mp4 files. ex: -si 'inputfiles/myscreen1.mp4' -si 'inputfiles/myscreen2.mp4' etc",
)
parser.add_argument(
    "-j", "--jump-cuts", action="store_true", help="do automatic jump cuts of dead air"
)
parser.add_argument(
    "-jm",
    "--jump-cuts-margin",
    metavar="seconds",
    type=float,
    default=0.75,
    help="The amount of silence to look for x2. defaults to 0.75 so 1.5 seconds of silence is required to jumpcut",
)
parser.add_argument(
    "-au",
    "--audio-podcast-enhancements",
    action="store_true",
    help="enhance the audio using some standard podcast audio filters. Will enhance anything in the output folder that is the --output-name or final.mp4 by default",
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
    type=float,
    help="Create a short starting at this second for 1 minute or until --till is set. Ex: --short 127 --till 148 (ie, create a 21 second short starting at 127 seconds in until 148s)",
)
parser.add_argument(
    "-ti",
    "--till",
    type=float,
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
    help="set the output to 1080p. Defaults to false",
    default=False,
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
    help="The name of the file to generate in the output folder, without the extension",
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
    help="the video to caption and csv with the same name as the video, so 'inputfiles/myvideo.mp4' would need inputfiles/myvideo.mp4.csv to exist. Use -tf to generate the csv. Example: -cv 'inputfiles/myvideo.mp4'",
    default="",
)
parser.add_argument(
    "-ct",
    "--caption-type",
    type=int,
    metavar="caption_type",
    help="the type of captions. 1: across the screen, 2: multiline",
    default=1,
)
parser.add_argument(
    "-f",
    "--font",
    type=str,
    metavar="FONT",
    help="the font used for the captions. Unfortunately it needs to be the full path, like '/usr/share/fonts/opentype/urw-base35/NimbusMonoPS-Bold.otf' or some local otf file you've downloaded",
    default="./FreeMonospacedBold.otf",
)
parser.add_argument(
    "-fs",
    "--font-size",
    type=int,
    help="The font size for captions",
    default=60,
)
parser.add_argument(
    "-cp",
    "--caption-position",
    type=str,
    metavar='"x, y"',
    help='The top left corner in pixels to place the captions, like -cp "200, 100" would be 200 pixels over, 100 pixels down',
    default="",
)
parser.add_argument(
    "-cd",
    "--collage-dir",
    type=str,
    metavar="DIR",
    help="The directory with a bunch of jpg or png images that will be fadded in and out to create a video",
)
parser.add_argument(
    "-ci",
    "--collage-input",
    type=str,
    metavar="VIDEO",
    help="the mp4 file to add the college to",
)

args = parser.parse_args()

print(args)

options = parse_cli_args(args)

if __name__ == "__main__":
    run(options)
