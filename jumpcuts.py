import subprocess


def apply_jumpcuts(vids: list[str], margin: float, use_hires: bool, output_name: str):
    for vid in vids:
        command = (
            f"auto-editor {vid} --margin {margin}sec --no-open "
            "--extras '-c:v libx264 -c:a aac -preset slow -b:v 3000k -maxrate 3000k -bufsize 6000k' "
            f"-o output/{output_name}-jumpcut.mp4"
        )

        if use_hires:
            command += " -res 1920,1080"

        subprocess.run(command, shell=True)
