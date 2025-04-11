import os
import sys
import time
import requests
from pytube import YouTube
import yt_dlp

def download_audio_from_youtube(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'audio.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return "audio.mp3"

# # Download the audio from the given YouTube URL
# def download_audio_from_youtube(url):
#     yt = YouTube(url)
#     stream = yt.streams.filter(only_audio=True).first()
#     output_file = stream.download(filename="audio.mp4")
#     return output_file

# Upload the audio file to AssemblyAI in chunks
def upload_audio(file_path, headers):
    upload_url = "https://api.assemblyai.com/v2/upload"
    
    def read_file(filename, chunk_size=5242880):  # 5MB chunks
        with open(filename, 'rb') as f:
            while True:
                data = f.read(chunk_size)
                if not data:
                    break
                yield data

    response = requests.post(upload_url, headers=headers, data=read_file(file_path))
    if response.status_code == 200:
        return response.json()['upload_url']
    else:
        print("Error uploading file:", response.text)
        sys.exit(1)

# Request a transcription with speaker labels and auto chapters enabled
def request_transcription(audio_url, headers):
    endpoint = "https://api.assemblyai.com/v2/transcript"
    json_data = {
        "audio_url": audio_url,
        "speaker_labels": True,
        "auto_chapters": True
    }
    response = requests.post(endpoint, json=json_data, headers=headers)
    if response.status_code == 200:
        return response.json()['id']
    else:
        print("Error requesting transcription:", response.text)
        sys.exit(1)

# Poll the transcription endpoint until the transcript is complete
def poll_transcription(transcript_id, headers):
    endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
    while True:
        response = requests.get(endpoint, headers=headers)
        result = response.json()
        status = result.get('status')
        if status == 'completed':
            return result
        elif status == 'error':
            print("Error in transcription:", result.get('error'))
            sys.exit(1)
        else:
            print("Transcription status:", status)
            time.sleep(10)

# Helper to convert milliseconds to hh:mm:ss or mm:ss
def convert_ms_to_time(ms):
    seconds = int(ms / 1000)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02}:{m:02}:{s:02}"
    else:
        return f"{m:02}:{s:02}"

# Generate a markdown file with transcript segments and chapters
def generate_markdown(transcription_result, output_filename="transcript.md"):
    md_lines = []
    md_lines.append("# Transcript for YouTube Video")
    md_lines.append("")
    md_lines.append("## Transcript Segments")
    md_lines.append("")
    if "utterances" in transcription_result:
        for utt in transcription_result["utterances"]:
            start_time = convert_ms_to_time(utt["start"])
            end_time = convert_ms_to_time(utt["end"])
            speaker = utt.get("speaker", "Unknown")
            text = utt["text"]
            md_lines.append(f"- **[{start_time} - {end_time}] Speaker {speaker}:** {text}")
    else:
        md_lines.append(transcription_result.get("text", "No transcript available."))
    md_lines.append("")
    ### -- This section is for the 'Chapters' in the output MD file, I think they take time, cost a lot, and are not necessary. -- ###
    # if "chapters" in transcription_result and transcription_result["chapters"]:
    #     md_lines.append("## Chapters")
    #     md_lines.append("")
    #     for idx, chapter in enumerate(transcription_result["chapters"], start=1):
    #         start_time = convert_ms_to_time(chapter["start"])
    #         end_time = convert_ms_to_time(chapter["end"])
    #         gist = chapter.get("gist", "No gist")
    #         summary = chapter.get("summary", "No summary")
    #         md_lines.append(f"### Chapter {idx}")
    #         md_lines.append(f"- **Time:** {start_time} - {end_time}")
    #         md_lines.append(f"- **Gist:** {gist}")
    #         md_lines.append(f"- **Summary:** {summary}")
    #         md_lines.append("")
    ### -- Section ends -- ###
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"Transcript saved to {output_filename}")

def main():
    # Set your AssemblyAI API key here or via the ASSEMBLYAI_API_KEY environment variable
    API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
    headers = {"authorization": API_KEY}
    
    if len(sys.argv) < 2:
        print("Usage: python script.py <YouTube Video URL>")
        sys.exit(1)
    
    youtube_url = sys.argv[1]
    
    print("Downloading audio from YouTube...")
    audio_file = download_audio_from_youtube(youtube_url)
    print("Audio downloaded to", audio_file)
    
    print("Uploading audio to AssemblyAI...")
    audio_url = upload_audio(audio_file, headers)
    print("Audio uploaded. URL:", audio_url)
    
    print("Requesting transcription...")
    transcript_id = request_transcription(audio_url, headers)
    print("Transcription requested. ID:", transcript_id)
    
    print("Polling transcription...")
    result = poll_transcription(transcript_id, headers)
    
    print("Generating markdown transcript...")
    generate_markdown(result)
    
if __name__ == "__main__":
    main()