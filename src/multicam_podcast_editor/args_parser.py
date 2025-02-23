from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class Args:
    multicam: bool = False
    short: float | None = None
    till: float | None = None
    cut: List[Tuple[float, float]] | None = None
    caption_video: bool = False
    caption_csv: str | None = None
    caption_position: Tuple[int, int] | None = None
    caption_size: Tuple[int, int] | None = None
    collage: bool = False
    inputs: List[str] = field(default_factory=list)
    screenshare_input: List[str] = field(default_factory=list)
    jump_cuts: bool = False
    jump_cuts_margin: float = 0.75
    audio_podcast_enhancements: bool = False
    audio_music_enhancements: bool = False
    transcribe: bool = False
    skip_bitrate_sync: bool = False
    threads: int = 10
    word_pause: float = 1.2
    hi_def: bool = False
    align_videos: bool = True
    output_name: str = "final"
    caption_type: int = 1
    font: str = "./FreeMonospacedBold.otf"
    font_size: int = 60
    music_video: bool = False
    thumbnail: str = ""
    seed: int = -1


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

    if args.screenshare_input is not None and len(args.screenshare_input) > 0:
        screenshares = sum(args.screenshare_input, [])
    else:
        screenshares = []

    inputs = []
    if args.input is not None and len(args.input) > 0:
        inputs: List[str] = sum(args.input, [])

    return Args(
        multicam=args.multicam,
        inputs=inputs,
        screenshare_input=screenshares,
        short=args.short,
        till=args.till,
        cut=args.cut,
        jump_cuts=args.jump_cuts,
        jump_cuts_margin=args.jump_cuts_margin,
        caption_video=args.caption_video,
        caption_csv=args.caption_csv,
        caption_position=int_pos,
        caption_size=int_size,
        audio_podcast_enhancements=args.audio_podcast_enhancements,
        audio_music_enhancements=args.audio_music_enhancements,
        transcribe=args.transcribe,
        skip_bitrate_sync=args.skip_bitrate_sync,
        threads=args.threads,
        word_pause=args.word_pause,
        align_videos=args.align_videos,
        output_name=args.output_name,
        hi_def=args.hi_def,
        caption_type=args.caption_type,
        font=args.font,
        font_size=args.font_size,
        music_video=args.music_video,
        thumbnail=args.thumbnail,
        seed=args.seed,
    )
