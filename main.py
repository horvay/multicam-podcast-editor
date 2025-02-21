import argparse

from args_parser import parse_cli_args
from orchestrate import run
from tprint import print_decorator

print = print_decorator(print)


parser = argparse.ArgumentParser(
    description="A cli to automatically multicam edit, jump cut, transcribe and interact with your podcast with an LLM"
)
parser.add_argument(
    "-i",
    "--input",
    action="append",
    nargs="+",
    help="General input. See other options for how to use it like -m, -s, -cv, etc",
)
parser.add_argument(
    "-m",
    "--multicam",
    action="store_true",
    help="do automatic multicam edits. Must include input files with -i. The first input file should be the main file with all camera/audio, and the following should be the invididual camera/audio. Ex: -m -i combined_vid.mp4 -i person1.mp4 -i person2.mp4 -i person3.mp4",
)
parser.add_argument(
    "-si",
    "--screenshare-input",
    action="append",
    nargs="+",
    help="Used for adding screenshare videos used in the multicam scenarios. Use -i for the combined and individuals' mp4s, and this for screenshare mp4s. ex: -si 'inputfiles/myscreen1.mp4' -si 'inputfiles/myscreen2.mp4' etc",
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
    "-ape",
    "--audio-podcast-enhancements",
    action="store_true",
    help="enhance the audio using some standard podcast audio filters. Will enhance anything in the output folder that is the --output-name or final.mp4 by default",
)
parser.add_argument(
    "-ame",
    "--audio-music-enhancements",
    action="store_true",
    help="enhance the audio using some standard music audio filters. Will enhance anything in the output folder that is the --output-name or final.mp4 by default",
)
parser.add_argument(
    "-t",
    "--transcribe",
    action="store_true",
    help="transcribe the podcast to a text file. If given 1 input file, it'll transcribe to a csv for captioning. If multiple input files, it'll assume it's the whole multicam setup (see multicam option for how to provide inputs)",
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
    "-o",
    "--output-name",
    type=str,
    help="The name of the file to generate in the output folder, without the extension",
    default="final",
)
parser.add_argument(
    "-cv",
    "--caption-video",
    action="store_true",
    help="caption a video. Requires the video to caption as an input, ie, -cv -i /video/to/caption.mp4",
    default=False,
)
parser.add_argument(
    "-csv",
    "--caption-csv",
    type=str,
    metavar="csv",
    help="the csv to go along with the video being captioned. Created by the --transcribe-file command though technically can be done by hand",
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
    "-cs",
    "--caption-size",
    type=str,
    metavar='"x, y"',
    help='The width and hight of the area the captions display, like -cp "300, 500" would be 300 pixels width, 500 pixels height. Defaults will try to fit it somewhere (good luck)',
    default="",
)

parser.add_argument(
    "-co",
    "--collage",
    action="store_true",
    help="Takes an existng mp4 file and displays images evenly throughout the video. The first input is the mp4 file to add images to, and the second is the dictory with images, ex, -co -i /path/to/mp4 -i /path/to/imgs/dir",
    default=False,
)

parser.add_argument(
    "-mv",
    "--music-video",
    action="store_true",
    help="Takes a folder of music, art, and optionally reminders (images that show sometimes) directories, and puts them together. The format would be -mv -i /music/dir -i /art/dir -i /remiders/dir",
    default=False,
)

parser.add_argument(
    "-th",
    "--thumbnail",
    type=str,
    metavar="path",
    help="path to a thumbnail to use when creating a video. Works for music videos right now. Adds it to the beginning for 1 second",
    default="",
)

parser.add_argument(
    "-se",
    "--seed",
    type=int,
    help="seed used for all random logic",
    default=-1,
)

args = parser.parse_args()

print(args)

options = parse_cli_args(args)

if __name__ == "__main__":
    run(options)
