# Multicam Podcast Editor

A command-line tool designed to automate video editing tasks, with a focus on podcasts, multicam recordings, and creative video projects. It uses audio analysis and advanced editing techniques to simplify the creation of professional-quality videos with minimal manual effort.

## Features

- **Automatic Multicam Editing**: Seamlessly switches between multiple camera angles based on audio levels, highlighting the active speaker or key moments.
- **Short Format Multicam Editing**: Generates concise clips from multicam setups, perfect for highlights or social media.
- **Video Cutting**: Allows precise removal of unwanted segments by specifying time ranges.
- **Automatic Jumpcuts**: Detects and eliminates pauses to improve pacing.
- **Transcription and Captioning**: Transcribes audio and adds customizable captions.
- **Music Video Creation**: Combines images and MP3s into music videos with transitions.
- **Audio Enhancements**: Applies filters for improved audio quality (e.g., noise reduction, equalization).

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/horvay/multicam-podcast-editor.git
   ```

2. **Install Dependencies**:
   Use `uv` to install the required Python packages:
   ```bash
   uv sync
   ```

   Install `ffmpeg` and `auto-editor` for audio/video processing:
   ```bash
   # On Ubuntu/Debian
   sudo apt-get install ffmpeg
   # On macOS with Homebrew
   brew install ffmpeg
   # Install auto-editor
   uv pip install auto-editor
   ```

3. **Verify Setup**:
   Check that everything works by running:
   ```bash
   uv run main.py -h
   ```
   This shows the help menu with command-line options.

## Usage

Run the tool with `uv run main.py` followed by specific flags and arguments. For all options, use:
```bash
uv run main.py -h
```

### Automatic Multicam Editing

Edit a multicam video with a main video and individual angles:
```bash
uv run main.py -m -i combined_vid.mp4 -i person1.mp4 -i person2.mp4 -i person3.mp4
```
- `-m`: Multicam editing mode.
- `-i`: Input files (first is the main video, followed by angles).

Add screenshare videos:
```bash
uv run main.py -m -i combined_vid.mp4 -i person1.mp4 -i person2.mp4 -si screenshare1.mp4
```

### Short Format Multicam Editing

Create a short clip with a start time (and optional end time):
```bash
uv run main.py -s 127 -ti 148 -i combined_vid.mp4 -i person1.mp4 -i person2.mp4
```
- `-s`: Start time (seconds).
- `-ti`: End time (seconds; defaults to 60 seconds after start if omitted).

### Cutting Videos

Remove segments by specifying time ranges:
```bash
uv run main.py -c 1.0 2.0 -c 3.0 4.0 -i input_video.mp4
```
- `-c`: Start and end times (seconds) to cut.

### Automatic Jumpcuts

Remove pauses:
```bash
uv run main.py -j -i input_video.mp4
```
- `-j`: Jumpcut mode.
- Adjust silence threshold (default 0.75 seconds):
```bash
uv run main.py -j --jump-cuts-margin 0.5 -i input_video.mp4
```

### Transcription and Captioning

#### Transcribe a Video
Generate a transcript:
```bash
uv run main.py -t -i input_video.mp4
```
- `-t`: Saves transcript to `output/input_video.mp4.csv`.

For multicam, create a chat-style transcript:
```bash
uv run main.py -t -i combined_vid.mp4 -i person1.mp4 -i person2.mp4
```
- Output: `output/transcript.txt`.

#### Add Captions
Add captions using a CSV:
```bash
uv run main.py -cv -i input_video.mp4 -csv output/input_video.mp4.csv
```
- `-cv`: Captioning mode.
- `-csv`: Transcription CSV file.

Customize captions:
```bash
uv run main.py -cv -i input_video.mp4 -csv output/input_video.mp4.csv -ct 2 -cp "200, 100" -cs "300, 500" -fs 80
```
- `-ct`: Caption type (1: across, 2: multiline).
- `-cp`: Position (x, y).
- `-cs`: Size (width, height).
- `-fs`: Font size.

### Music Video Creation

Create a music video from directories:
```bash
uv run main.py -mv -i music_dir -i art_dir -i reminders_dir -th thumbnail.png
```
- `-mv`: Music video mode.
- `-i`: Directories for music, art, reminders.
- `-th`: Optional thumbnail.

### Audio Enhancements

Enhance audio for podcasts:
```bash
uv run main.py -ape -i input_video.mp4
```
- `-ape`: Podcast enhancements.

For music:
```bash
uv run main.py -ame -i input_video.mp4
```
- `-ame`: Music enhancements.

## Additional Notes

- **Output Files**: Saved in `output/` with names like `final_<random>.mp4` (customizable via `--output-name`).
- **Temporary Files**: Processed in `temp/`, cleared each run.
- **Customization**: Use `--threads` (default: 10) or `--hi-def` for 1080p.

