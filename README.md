# Multicam Podcast Editor
If you use an app like streamyards, they provide the main podcast video, and then separate individual video files for each person attending your streamyard session. 

I've created a tool to automatically do 2 things:
1. Synchronize the videos to the main multipeople video. The individuals' files are always slightly off in their timing.
2. Chunk the file videos into 5 second segments and use the individuals' video if they are mostly the only one talking for those 5 seconds.
3. Use jump cutting to remove dead air

### Dependencies
- ffmpeg
- https://github.com/WyattBlue/auto-editor
- https://github.com/align-videos-by-sound/align-videos-by-sound

### installation

1. Install ffmpeg and ensure it's in your path
1. Install auto-editor and align-videos-by-sound as per their github page
1. run the following
```bash
git clone this-repo
cd this-repo
pip install -r requirements.txt
```

* note, you may want to make a conda environment first

### Usage

This tool assumes you have 2 or more files: a video with all the audio and video from all the participants, and individual videos for each participant.
You will need to follow this naming exactly:
- call the video with all the cameras and audios "main.mp4"
- call each of the individuals' videos "person1.mp4", "person2.mp4", etc

Ensure these videos are in the same directory as this tool.

Run the following:
```bash
python main.py
```

It will take quite some time to run but should give updates on it's progress.

### Compatibility
- Confirmed working on Windows 10, have not confirmed on other operating systems
