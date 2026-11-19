# ai-video-clipper

An automated Python tool that downloads a video from a URL, transcribes/translates the audio into English, uses Gemini AI to detect the most engaging segment, and exports a trimmed video with burned-in English subtitles.

## How to Run on Mobile (Google Colab)

1. Open [Google Colab](https://google.com) and create a **New Notebook**.
2. Paste and run the following code in a cell (replace `YOUR_USERNAME` and `YOUR_GEMINI_API_KEY`):

```python
!git clone https://github.com
%cd ai-video-clipper
!pip install -q -r requirements.txt

import os
os.environ["GEMINI_API_KEY"] = "YOUR_GEMINI_API_KEY"
!python main.py
```

3. Paste your video link when prompted.
4. Run this in a new cell to download the finished video to your phone:

```python
from google.colab import files
files.download("final_clip.mp4")
```
