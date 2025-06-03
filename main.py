from multicam_podcast_editor.args_parser import (
    build_parser,
    parse_cli_args,
)
from multicam_podcast_editor.orchestrate import run
from multicam_podcast_editor.tprint import print_decorator

print = print_decorator(print)

parser = build_parser()
args = parser.parse_args()

print(args)

options = parse_cli_args(args)

if __name__ == "__main__":
    run(options)
