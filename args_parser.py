from dataclasses import dataclass, field
from typing import List, Tuple
from glob import glob


@dataclass
class Args:
    multicam: bool = False
    short: float | None = None
    till: float | None = None
    cut: List[Tuple[float, float]] | None = None
    transcribe_file: str | None = None
    caption_video: str | None = None
    caption_csv: str | None = None
    question: str | None = None
    caption_position: Tuple[int, int] | None = None
    caption_size: Tuple[int, int] | None = None
    collage_dir: str | None = None
    collage_input: str | None = None
    screenshare_input: List[str] = field(default_factory=list)
    jump_cuts: bool = False
    jump_cuts_margin: float = 0.75
    multicam_main_vid: str = "main.mp4"
    multicam_input: List[str] = field(default_factory=list)
    audio_enhancements: bool = False
    transcribe: bool = False
    skip_bitrate_sync: bool = False
    threads: int = 10
    word_pause: float = 1.2
    ignore_screenshares: bool = False
    hi_def: bool = False
    align_videos: bool = True
    output_name: str = "final"
    model: str = "llama3.2-vision"
    caption_type: int = 1
    font: str = "./FreeMonospacedBold.otf"
    font_size: int = 60
    music_video_music: str | None = None
    music_video_art: str | None = None
    music_video_reminders: str | None = None


def _get_positon_param(pos_param: str):
    coordinates = pos_param.split(",")
    if len(coordinates) != 2:
        raise Exception(
            "invalid position parameter. Must be two values separated by a comma with the whole thing in quotes"
        )
    try:
        x, y = int(coordinates[0]), int(coordinates[1])
    except ValueError:
        raise Exception("coordinates must be integers")

    return (x, y)


def parse_cli_args(args):
    str_pos = args.caption_position
    str_size = args.caption_size
    int_pos = None
    int_size = None
    if str_pos is not None and str_pos != "":
        int_pos = _get_positon_param(str_pos)

    if str_size is not None and str_size != "":
        int_size = _get_positon_param(str_size)

    if args.ignore_screenshares:
        screenshares = []
    elif args.screenshare_input is not None and len(args.screenshare_input) > 0:
        screenshares = sum(args.screenshare_input, [])
    else:
        screenshares = glob("inputfiles/*screen*.mp4")

    if args.multicam_input is not None and len(args.multicam_input) > 0:
        individuals: List[str] = sum(args.multicam_input, [])
    else:
        individuals: List[str] = glob("inputfiles/person*.mp4") + glob(
            "inputfiles/*webcam*.mp4"
        )

    return Args(
        multicam=args.multicam,
        multicam_main_vid=args.multicam_main_vid,
        multicam_input=individuals,  # pyright: ignore
        screenshare_input=screenshares,  # pyright: ignore
        collage_dir=args.collage_dir,
        collage_input=args.collage_input,
        short=args.short,
        till=args.till,
        cut=args.cut,
        jump_cuts=args.jump_cuts,
        jump_cuts_margin=args.jump_cuts_margin,
        transcribe_file=args.transcribe_file,
        caption_video=args.caption_video,
        caption_csv=args.caption_csv,
        question=args.question,
        caption_position=int_pos,
        caption_size=int_size,
        audio_enhancements=args.audio_podcast_enhancements,
        transcribe=args.transcribe,
        skip_bitrate_sync=args.skip_bitrate_sync,
        threads=args.threads,
        word_pause=args.word_pause,
        ignore_screenshares=args.ignore_screenshares,
        align_videos=args.align_videos,
        output_name=args.output_name,
        model=args.model,
        hi_def=args.hi_def,
        caption_type=args.caption_type,
        font=args.font,
        font_size=args.font_size,
        music_video_music=args.music_video_music,
        music_video_art=args.music_video_art,
        music_video_reminders=args.music_video_reminders,
    )
