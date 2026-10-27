# 🎥 AI Video Assistant

An AI-powered video assistant that converts video content into searchable and interactive knowledge. The application accepts YouTube URLs or local video files, extracts and transcribes the audio using Whisper, stores the transcript as vector embeddings, and uses Retrieval-Augmented Generation (RAG) with a Groq-powered LLM to answer questions about the video.

## 🚀 Features

- 🎬 Process videos from YouTube URLs or local video files
- 🎵 Extract audio from videos using `yt-dlp`
- 🗣️ Transcribe audio using OpenAI Whisper
- 🌐 Support for English and Hinglish content
- ✂️ Split transcripts into manageable chunks
- 🔎 Perform semantic search over video transcripts
- 🧠 RAG-based question answering
- 🗄️ Store and retrieve embeddings using ChromaDB
- 🤖 Generate context-aware answers using Groq LLMs
- 📝 Automatically generate concise video summaries
- 🏷️ Generate AI-powered video titles
- ⚡ Fast LLM inference using Groq

## 🏗️ Architecture

```text
YouTube URL / Local Video
          │
          ▼
       yt-dlp
          │
          ▼
    Audio Extraction
          │
          ▼
       Whisper
          │
          ▼
      Transcript
          │
          ▼
    Text Chunking
          │
          ▼
      Embeddings
          │
          ▼
       ChromaDB
          │
          ▼
    Semantic Retrieval
          │
          ▼
       Groq LLM
          │
          ▼
   Answer / Summary / Title
```

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Whisper | Speech-to-text transcription |
| yt-dlp | YouTube/video processing |
| LangChain | LLM and RAG workflow |
| ChromaDB | Vector database |
| Groq | Fast LLM inference |
| Python-dotenv | Environment variable management |

## 📋 Requirements

- Python 3.10+
- FFmpeg
- Groq API key
- Internet connection for YouTube videos and API-based services

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/Sarfaraj111/ai-video-assistant.git
cd ai-video-assistant
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv .venv
```

Git Bash:

```bash
source .venv/Scripts/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 🔑 Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
```

Never commit your `.env` file or expose your API key publicly.

A `.env.example` file can be used as a template:

```env
GROQ_API_KEY=your_groq_api_key_here
```

## ▶️ Running the Application

Run the application using:

```bash
python main.py
```

Depending on the configured interface, provide either:

```text
YouTube URL
```

or:

```text
Local video file path
```

The application processes the video, generates a transcript, creates the required vector representations, and allows the transcript to be queried using the LLM.

## 💬 Example Workflow

```text
Input:
https://www.youtube.com/watch?v=example

        ↓

Download / Extract Audio

        ↓

Whisper Transcription

        ↓

Transcript Chunking

        ↓

Vector Embeddings

        ↓

ChromaDB

        ↓

User Question

        ↓

Relevant Transcript Retrieval

        ↓

Groq LLM

        ↓

Context-Aware Answer
```

## 🧠 RAG Implementation

The project uses Retrieval-Augmented Generation to reduce the need to send the entire transcript to the LLM for every question.

The workflow is:

1. Transcribe the video.
2. Split the transcript into smaller chunks.
3. Generate embeddings for the chunks.
4. Store the embeddings in ChromaDB.
5. Retrieve the most relevant chunks for a user's question.
6. Provide the retrieved context to the Groq LLM.
7. Generate an answer based on the retrieved video content.

This allows users to ask questions about specific information contained within long videos.

## 📌 Example Questions

After processing a video, users can ask questions such as:

```text
What are the main points discussed in this video?

Summarize the video in 5 points.

What problem does the speaker discuss?

Explain the concept mentioned in the second half of the video.

What conclusion does the speaker reach?
```

## 🔒 Security

API keys and other sensitive information should never be committed to GitHub.

This project uses `.gitignore` to exclude:

```text
.env
.venv/
vector_db/
chroma_db/
*.mp3
*.wav
*.mp4
*.webm
```

## 🔮 Future Improvements

- Add a Streamlit web interface
- Support multiple video uploads
- Add timestamp-based answers
- Generate downloadable PDF summaries
- Add multilingual transcription
- Add conversation memory
- Improve long-video processing
- Add video chapter/section generation
- Deploy the application to the cloud

## 👨‍💻 Author

**MD Sarfaraj**

B.Tech Computer Science & Engineering

Interested in AI/ML, Generative AI, RAG, Data Science and AI Engineering.

## ⭐ If you find this project useful

Give the repository a ⭐ on GitHub!
