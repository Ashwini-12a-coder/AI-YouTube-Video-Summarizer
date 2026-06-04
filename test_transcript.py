from youtube_transcript_api import YouTubeTranscriptApi

video_id = "6zOyOglWGw4"

try:
    transcript = YouTubeTranscriptApi().fetch(
        video_id,
        languages=["en"]
    )

    print("SUCCESS")
    print("First line:")
    print(transcript[0].text)

except Exception as e:
    print("FAILED")
    print(e)