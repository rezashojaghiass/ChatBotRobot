# How to Get Madagascar Subtitle File

The Madagascar quiz mode requires a subtitle file (.srt format) to use as the knowledge base for RAG (Retrieval-Augmented Generation).

## Legal Notice

**⚠️ Copyright Disclaimer:**
- Movie subtitles are copyrighted material
- We do NOT include the subtitle file in this repository
- You must obtain subtitles legally for personal use only
- This is for educational purposes

## Option 1: Download from Legal Sources

### OpenSubtitles.org (Recommended)
```
1. Go to: https://www.opensubtitles.org/
2. Create free account
3. Search: "Madagascar 2005 English"
4. Download .srt file
5. Save to: /mnt/nvme/adrian/ChatBotRobot/data/Madagascar.srt
```

### Subscene.com
```
1. Go to: https://subscene.com/
2. Search: "Madagascar 2005"
3. Select English subtitles
4. Download and extract .srt file
5. Save to: /mnt/nvme/adrian/ChatBotRobot/data/Madagascar.srt
```

### YIFY Subtitles
```
1. Go to: https://yts-subs.com/
2. Search: "Madagascar 2005"
3. Download English .srt
4. Save to: /mnt/nvme/adrian/ChatBotRobot/data/Madagascar.srt
```

## Option 2: Extract from DVD/Blu-ray (if you own it)

### Using MakeMKV
```bash
# 1. Install MakeMKV (trial available)
# https://www.makemkv.com/

# 2. Insert Madagascar DVD/Blu-ray
# 3. Select English subtitle track
# 4. Extract to .srt format

# 5. Save to data directory
cp /path/to/extracted/Madagascar.srt /mnt/nvme/adrian/ChatBotRobot/data/
```

### Using ffmpeg (if you have .mkv file)
```bash
# Check subtitle streams
ffmpeg -i Madagascar.mkv

# Extract first English subtitle
ffmpeg -i Madagascar.mkv -map 0:s:0 /mnt/nvme/adrian/ChatBotRobot/data/Madagascar.srt

# If multiple subtitle tracks:
ffmpeg -i Madagascar.mkv -map 0:s:1 Madagascar.srt  # Try different index
```

## Option 3: Use Sample Subtitles (for testing)

If you just want to test the system, create a small sample:

```bash
cd /mnt/nvme/adrian/ChatBotRobot/data

cat > test_subtitles.srt << 'EOF'
1
00:00:01,000 --> 00:00:03,500
I'm 10 years old today!
Can you believe it?

2
00:00:03,600 --> 00:00:05,200
Happy birthday, Marty!

3
00:00:05,300 --> 00:00:08,000
Alex, do you ever wonder
what's out there?

4
00:00:08,100 --> 00:00:09,500
Out where?

5
00:00:09,600 --> 00:00:12,000
You know, out there.
Beyond the zoo.

6
00:00:12,100 --> 00:00:14,000
What are you talking about?

7
00:00:14,100 --> 00:00:17,000
The wild, Alex.
Don't you ever think about the wild?

8
00:00:17,100 --> 00:00:19,000
I'm a zoo animal.
The zoo is my home.

9
00:00:19,100 --> 00:00:21,000
But we're from the wild originally.

10
00:00:21,100 --> 00:00:23,000
That was like a million years ago.

11
00:00:23,100 --> 00:00:26,000
This is the best birthday ever!

12
00:00:26,100 --> 00:00:28,500
You're the best friend
a zebra could ask for.

13
00:00:28,600 --> 00:00:30,000
Happy birthday, buddy.

14
00:00:30,100 --> 00:00:31,500
Thanks, Alex.

15
00:00:31,600 --> 00:00:34,000
Marty, you can't just run away!

16
00:00:34,100 --> 00:00:36,500
But I want to see the wild, Alex!

17
00:00:36,600 --> 00:00:39,000
The wild is dangerous, Marty!

18
00:00:39,100 --> 00:00:41,500
I don't care, I want an adventure!

19
00:00:41,600 --> 00:00:44,000
We ended up in Madagascar!

20
00:00:44,100 --> 00:00:46,500
This is crazy! Where are we?
EOF

# Test with sample file:
cd ../src
python3 voice_chat_riva_aws.py --subtitle ../data/test_subtitles.srt --rag --mode madagascar_quiz --llm llama
```

## Option 4: Use Different Movie

The system works with ANY movie subtitle file! Just change the file:

```bash
# Download subtitles for any movie
# For example: Toy Story, Finding Nemo, The Lion King, etc.

# Save to:
/mnt/nvme/adrian/ChatBotRobot/data/YourMovie.srt

# Use with:
python3 voice_chat_riva_aws.py --subtitle ../data/YourMovie.srt --rag --mode madagascar_quiz --llm llama70b

# Note: The quiz will ask questions about the movie in the subtitle file
# You may want to rename --mode to match your movie, or just use "chat" mode
```

## Verify Subtitle File

After downloading, verify the format:

```bash
cd /mnt/nvme/adrian/ChatBotRobot/data

# Check first few lines
head -20 Madagascar.srt

# Should see format like:
# 1
# 00:00:01,000 --> 00:00:03,500
# Dialogue text here
# 
# 2
# 00:00:03,600 --> 00:00:05,200
# More dialogue
```

## Troubleshooting

### Wrong Format

If subtitle file is not .srt (e.g., .sub, .ass, .vtt):

```bash
# Convert using ffmpeg
ffmpeg -i subtitles.vtt subtitles.srt
ffmpeg -i subtitles.ass subtitles.srt

# Or use online converter:
# https://subtitletools.com/convert-to-srt-online
```

### Encoding Issues

If you see garbled characters:

```bash
# Convert to UTF-8
iconv -f ISO-8859-1 -t UTF-8 Madagascar.srt -o Madagascar_utf8.srt
mv Madagascar_utf8.srt Madagascar.srt
```

### Too Large

If subtitle file is huge (>10MB):

```bash
# Extract first 1000 dialogues only
head -4000 Madagascar.srt > Madagascar_small.srt
# (1000 dialogues × ~4 lines each = 4000 lines)
```

## Default Path Configuration

The application looks for subtitle file at:
```
/mnt/nvme/adrian/ChatBotRobot/data/Madagascar.srt
```

To use different path:
```bash
python3 voice_chat_riva_aws.py --subtitle /path/to/your/subtitles.srt --rag
```

## Questions?

If you have issues with subtitle files, check:
1. File exists: `ls -lh data/Madagascar.srt`
2. File is readable: `cat data/Madagascar.srt | head`
3. File format is correct (see "Verify Subtitle File" above)
4. File encoding is UTF-8: `file data/Madagascar.srt`

See [RAG_IMPLEMENTATION.md](RAG_IMPLEMENTATION.md) for how subtitle files are processed.
