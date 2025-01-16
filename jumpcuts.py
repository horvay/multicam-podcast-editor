import subprocess


def apply_jumpcuts(vids: list[str], margin: float, use_hires: bool, output_name: str):
    for vid in vids:
        command = (
            f"auto-editor {vid} --margin {margin}sec --no-open "
            "-c:v libopenh264 -c:a aac -b:v 3000k "
            f"-o output/{output_name}-jumpcut.mp4"
        )

        if use_hires:
            command += " -res 1920,1080"

        subprocess.run(command, shell=True)
