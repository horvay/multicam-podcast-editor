# Multicam Podcast Editor

<!--toc:start-->
- [Multicam Podcast Editor](#multicam-podcast-editor)
  - [Dependencies](#dependencies)
  - [installation](#installation)
  - [Usage](#usage)
  - [Compatibility](#compatibility)
<!--toc:end-->

If you use an app like streamyards, they provide the main podcast video, and then separate individual video files for each person attending your streamyard session.

I've created a tool to automatically do the following things:

1. Synchronize the videos to the main multipeople video. The individuals' files are always slightly off in their timing.
2. Chunk the file videos into 5 second segments and use the individuals' video if they are mostly the only one talking for those 5 seconds.
3. Use jump cutting to remove dead air
4. Transcribe the video using the individuals' videos
5. The ability to ask an LLM about your podcast/video transcription
6. Create shorts given a time range

## Dependencies

- ffmpeg
- <https://github.com/WyattBlue/auto-editor>
- <https://github.com/align-videos-by-sound/align-videos-by-sound>
- For chat, install ollama

## installation

1. Install ffmpeg and ensure it's in your path
1. Install auto-editor and align-videos-by-sound as per their github page
1. run the following

```bash
git clone https://github.com/horvay/multicam-podcast-editor
cd multicam-podcast-editor
pip install -r requirements.txt
```

- note, you may want to make a conda environment first

## Usage

This tool assumes you have 2 or more files: a video with all the audio and video from all the participants, and individual videos for each participant.
You will need to follow this naming exactly:

- call the video with all the cameras and audios "main.mp4"
- call each of the individuals' videos "person1.mp4", "person2.mp4", etc, or have the word "webcam" in the name. (this is because individual files in streamyard have the name webcam so I can just copy and paste them)
- if you want to include screenshares, then copy those over and ensure they have the word "screen" in them.

Ensure these videos are in the same directory as this tool, and that none of the files have parenthesis in them. align-videos-by-sound doesn't seem to handle ().

Run the following for multicam editing

```bash
python main.py --multicam
```

or for transcribing

```bash
python main.py --transcribe
```

run the following to see all options

```bash
python main.py --help
```

For instance, if you wanted to do automatic multicam editing including jump cuts to remove deadair, transcribe the videos into a text file, and then ask for youtube titles about your videos, you could do the following:

```bash
python main.py --multicam --jump-cuts --transcribe --question "what are some good youtube titles for this podcast?"
```

This would give you the final edited video outputted to the directory, a transcript.txt file, and it would output the console the response to your question, using an ollama LLM (llama3.2 by default)

The following will create a short from the videos in the directory, starting at second 1705 until second 1812, it'll remove the deadair and will cut out seconds 50.1-67.0, 88.5-96.0, etc.

```python
python main.py -s 1705 -ti 1812 --jump-cuts -c 50.1 67.0 -c 88.5 96.0 -c 9.5 103.0 
```

It will take quite some time to run but should give updates on it's progress.

## Compatibility

- I've only run this on linux but it should work for other environments since it's python
