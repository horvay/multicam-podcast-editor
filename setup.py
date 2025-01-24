from setuptools import setup, find_packages

setup(
    name="multicam-podcast-editor",  # Choose a concise and descriptive name
    version="0.1.0",  # Assign an initial version number
    packages=find_packages(),
    install_requires=[
        "audalign",
        "faster_whisper",
        "ffmpeg_normalize",
        "moviepy",
        "numpy",
        "ollama",
        "torch",
    ],
)
