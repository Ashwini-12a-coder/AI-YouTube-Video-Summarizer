from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

from sentence_transformers import SentenceTransformer
from transformers import pipeline

import faiss
import numpy as np


# -----------------------
# Get Video ID
# -----------------------
def get_video_id(url):
    if "youtu.be" in url:
        return url.split("/")[-1].split("?")[0]

    if "youtube.com" in url:
        return parse_qs(urlparse(url).query)["v"][0]

    raise ValueError("Invalid YouTube URL")


# -----------------------
# Get Transcript
# -----------------------
def get_transcript(video_id):
    try:
        api = YouTubeTranscriptApi()

        try:
            transcript = api.fetch(video_id, languages=["en"])
        except:
            print("English transcript not found. Trying Telugu...")
            transcript = api.fetch(video_id, languages=["te"])

        text = " ".join([item.text for item in transcript])

        return text

    except Exception as e:
        print("\nError fetching transcript:")
        print(e)
        return ""


# -----------------------
# Chunk Text
# -----------------------
def chunk_text(text, size=500):
    chunks = []

    for i in range(0, len(text), size):
        chunks.append(text[i:i + size])

    return chunks


# -----------------------
# Load Embedding Model
# -----------------------
print("Loading embedding model...")

embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)


# -----------------------
# Build FAISS
# -----------------------
def build_faiss(chunks):
    embeddings = embedding_model.encode(chunks)

    embeddings = np.array(embeddings).astype("float32")

    index = faiss.IndexFlatL2(
        embeddings.shape[1]
    )

    index.add(embeddings)

    return index


# -----------------------
# QA Model
# -----------------------
print("Loading QA model...")

qa = pipeline(
    "question-answering",
    model="distilbert-base-cased-distilled-squad"
)


# -----------------------
# Summary Model
# -----------------------
print("Loading Summary model...")

summarizer = pipeline(
    "summarization",
    model="sshleifer/distilbart-cnn-12-6"
)


# -----------------------
# Main
# -----------------------
youtube_url = input("\nEnter YouTube URL: ")

video_id = get_video_id(youtube_url)

print("\nFetching transcript...")

transcript_text = get_transcript(video_id)

if len(transcript_text) == 0:
    print("\nNo transcript available.")
    exit()

print("\nTranscript extracted successfully!")

chunks = chunk_text(transcript_text)

index = build_faiss(chunks)

print("\nReady! Ask questions")
print("Type 'summary' for summary")
print("Type 'key points' for key points")
print("Type 'speaker' for speaker")
print("Type 'exit' to stop\n")

while True:

    question = input("Ask: ")

    if question.lower() == "exit":
        break

    # -------------------
    # Summary
    # -------------------
    if question.lower() == "summary":

        print("\nGenerating summary...\n")

        try:
            text_for_summary = transcript_text[:3000]

            summary = summarizer(
                text_for_summary,
                max_length=150,
                min_length=50,
                do_sample=False
            )

            print(summary[0]["summary_text"])

        except Exception as e:
            print("Summary Error:", e)

        print()
        continue

    # -------------------
    # Key Points
    # -------------------
    if question.lower() == "key points":

        print("\nKey Points:\n")

        for i in range(min(5, len(chunks))):
            print(f"{i+1}. {chunks[i][:200]}")

        print()
        continue

    # -------------------
    # Speaker
    # -------------------
    if question.lower() == "speaker":

        first_part = transcript_text[:1000]

        if "my name is" in first_part.lower():

            start = first_part.lower().find("my name is")

            speaker_text = first_part[start:start+50]

            print("\nPossible Speaker:")
            print(speaker_text)

        else:
            print("\nSpeaker not clearly identified.")

        print()
        continue

    # -------------------
    # Normal Q&A
    # -------------------
    query_embedding = embedding_model.encode(
        [question]
    )

    query_embedding = np.array(
        query_embedding
    ).astype("float32")

    D, I = index.search(
        query_embedding,
        k=3
    )

    context = ""

    for idx in I[0]:
        context += chunks[idx] + " "

    try:

        result = qa(
            question=question,
            context=context
        )

        print("\nAnswer:", result["answer"])
        print()

    except Exception as e:
        print("\nError:", e)