import os
import subprocess
import torch
import numpy as np
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from langchain_experimental.text_splitter import SemanticChunker
from langchain.schema.embeddings import Embeddings
from app.chains.generation_chain import GenerationChain
from app.utils.markdown_parser import parse_between_delimiters
import glob
import requests
import subprocess
import webbrowser
import re
import ast


from dotenv import load_dotenv
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")  


class VideoQA:
    def __init__(self, transcript_path, frames_dir, audio_path, video_path, screenshot_dir, interval=5, k_text=10, k_images=3):
        self.TRANSCRIPT_PATH = transcript_path
        self.FRAMES_DIR = frames_dir
        self.AUDIO_PATH = audio_path
        self.VIDEO_PATH = video_path
        self.SCREENSHOT_DIR = screenshot_dir
        self.INTERVAL = interval
        self.K_TEXT = k_text
        self.K_IMAGES = k_images

        # CLIP model
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(self.device)
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

    # --- DOWNLOAD ---
    def download_audio(self, url):
        print("📥 Downloading audio...")
        cmd = [
            "yt-dlp",
            "-f", "bestaudio",
            "--extract-audio",
            "--audio-format", "mp3",
            "--output", self.AUDIO_PATH,
            url
        ]
        subprocess.run(cmd, check=True)
    
    def transcribe_audio_groq(self, audio_path):
        print("🧠 Transcribing via Groq API (with timestamps)...")

        url = "https://api.groq.com/openai/v1/audio/transcriptions"

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}"
        }

        with open(audio_path, 'rb') as audio_file:
            files = {"file": audio_file}
            data = {
                "model": "whisper-large-v3",
                "response_format": "verbose_json"  # 👈 tells it to include timestamps
            }

            response = requests.post(url, files=files, data=data, headers=headers)
            response.raise_for_status()

            result = response.json()

        # Save raw JSON for later processing
        output_path = self.TRANSCRIPT_PATH
        json_path = output_path.replace(".txt", ".json")
        with open(json_path, "w", encoding="utf-8") as f:
            import json
            json.dump(result, f, ensure_ascii=False, indent=2)

        # Save plain text with timestamps
        with open(output_path, "w", encoding="utf-8") as out_file:
            for seg in result.get("segments", []):
                start = seg["start"]
                end = seg["end"]
                text = seg["text"].strip()
                out_file.write(f"[{start:.2f} - {end:.2f}] {text}\n")

        print(f"✅ Transcript with timestamps saved to {output_path}")
        print(f"📂 Full JSON saved to {json_path}")

    def download_video_and_screenshots(self, url):
        print("📥 Downloading video...")
        cmd = [
            "yt-dlp",
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "--merge-output-format", "mp4",
            "--output", self.VIDEO_PATH,
            url
        ]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to download video: {e}")
            return False

        self.capture_screenshots()
        return True

    def capture_screenshots(self):
        print(f"📸 Capturing screenshots every {self.INTERVAL} seconds...")
        os.makedirs(self.SCREENSHOT_DIR, exist_ok=True)

        drawtext_filter = f"drawtext=text='%{{eif\\:n*{self.INTERVAL}\\:d}}s':fontsize=20:fontcolor=white:x=10:y=10"
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", self.VIDEO_PATH,
            "-vf", f"fps=1/{self.INTERVAL},{drawtext_filter}",
            "-frame_pts", "1",
            os.path.join(self.SCREENSHOT_DIR, "temp_%04d.png")
        ]
        try:
            subprocess.run(ffmpeg_cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to capture screenshots: {e}")
            return False

        temp_files = sorted(glob.glob(os.path.join(self.SCREENSHOT_DIR, "temp_*.png")))
        for i, temp_file in enumerate(temp_files):
            timestamp = i * self.INTERVAL
            new_name = os.path.join(self.SCREENSHOT_DIR, f"frame_{timestamp}.png")
            os.rename(temp_file, new_name)

        print("🎯 Done! Screenshots saved in:", self.SCREENSHOT_DIR)

    # --- EMBEDDINGS ---
    class CLIPTextEmbeddings(Embeddings):
        def __init__(self, processor, model, device):
            self.processor = processor
            self.model = model
            self.device = device

        def embed_documents(self, texts):
            inputs = self.processor(text=texts, return_tensors="pt", padding=True, truncation=True).to(self.device)
            with torch.no_grad():
                embeddings = self.model.get_text_features(**inputs)
            return embeddings.cpu().numpy().tolist()

        def embed_query(self, text):
            inputs = self.processor(text=[text], return_tensors="pt", padding=True, truncation=True).to(self.device)
            with torch.no_grad():
                embeddings = self.model.get_text_features(**inputs)
            return embeddings.cpu().numpy()[0].tolist()

    def semantic_chunk_text(self, text):
        clip_embeddings = self.CLIPTextEmbeddings(self.processor, self.model, self.device)
        splitter = SemanticChunker(clip_embeddings)
        return splitter.split_text(text)

    def embed_text(self, text_list):
        inputs = self.processor(text=text_list, return_tensors="pt", padding=True, truncation=True).to(self.device)
        with torch.no_grad():
            embeddings = self.model.get_text_features(**inputs)
        return embeddings.cpu().numpy()

    def embed_images(self, image_paths):
        images = [Image.open(p).convert("RGB") for p in image_paths]
        inputs = self.processor(images=images, return_tensors="pt", padding=True).to(self.device)
        with torch.no_grad():
            embeddings = self.model.get_image_features(**inputs)
        return embeddings.cpu().numpy()

    def cosine_similarity(self, a, b):
        a = a / np.linalg.norm(a, axis=1, keepdims=True)
        b = b / np.linalg.norm(b, axis=1, keepdims=True)
        return np.dot(a, b.T)

    def build_context_with_frames(self, transcript_chunks, text_scores, frame_files, image_scores, best_text_indices, best_image_indices):
        top_transcripts = [
            f"[Transcript] {transcript_chunks[idx]} (score: {text_scores[idx]:.4f})"
            for idx in best_text_indices
        ]
        top_images = [frame_files[idx] for idx in best_image_indices]

        best_timestamp = None
        if best_text_indices.size > 0:
            first_chunk = transcript_chunks[best_text_indices[0]]
            if first_chunk.startswith("[") and "]" in first_chunk:
                ts_part = first_chunk.split("]")[0].strip("[")
                start_ts = ts_part.split("-")[0].strip()
                seconds = float(start_ts)
                hrs = int(seconds // 3600)
                mins = int((seconds % 3600) // 60)
                secs = int(seconds % 60)
                best_timestamp = f"{hrs:02}:{mins:02}:{secs:02}"

        context = (
            "Top Relevant Transcripts:\n" + "\n".join(top_transcripts) + "\n\n"
            "Top Retrieved Frames:\n" + "\n".join(top_images) + "\n\n"
            f"Best Timestamp: {best_timestamp if best_timestamp else 'N/A'}"
        )
        return context, top_images, best_timestamp

    # --- MAIN PIPELINE ---
    def run(self, url, query):
        if not os.path.exists(self.TRANSCRIPT_PATH):
            self.download_audio(url)
            self.download_video_and_screenshots(url)
            self.transcribe_audio_groq(audio_path=self.AUDIO_PATH)
        

        with open(self.TRANSCRIPT_PATH, "r") as f:
            transcript = f.read().strip()
        transcript_chunks = self.semantic_chunk_text(transcript)

        frame_files = sorted([
            os.path.join(self.FRAMES_DIR, f)
            for f in os.listdir(self.FRAMES_DIR)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        ])

        text_embeddings = self.embed_text(transcript_chunks)
        image_embeddings = self.embed_images(frame_files)

        query_embedding = self.embed_text([query])

        text_scores = self.cosine_similarity(query_embedding, text_embeddings)[0]
        image_scores = self.cosine_similarity(query_embedding, image_embeddings)[0]

        best_text_indices = np.argsort(text_scores)[::-1][:self.K_TEXT]
        best_image_indices = np.argsort(image_scores)[::-1][:self.K_IMAGES]

        context, top_images, best_timestamp = self.build_context_with_frames(
            transcript_chunks, text_scores, frame_files, image_scores, best_text_indices, best_image_indices
        )

        generation = GenerationChain()
        answer = generation.question_answering_video(question=query, context=context)

        print("\n=== LLM Answer ===\n", answer)
        print("\nRetrieved Images:", top_images)
        print("Best Timestamp:", best_timestamp)

        frames_paths = parse_between_delimiters(output=answer, delimiter="<<RETRIEVED_IMAGES>>")
        timestamp = parse_between_delimiters(output=answer, delimiter="<<BEST_TIMESTAMP>>")

        frames_paths = ast.literal_eval(frames_paths)

        for img in frames_paths:
            subprocess.Popen(["xdg-open", img])
        

        match = re.search(r"<<([\d\.]+)\s*-\s*[\d\.]+>>", timestamp)
        if match:
            start_seconds = float(match.group(1))
            # Convert seconds to integer for YouTube t parameter
            start_seconds_int = int(start_seconds)
            # Build YouTube URL with start time
            video_with_time = f"{url}&t={start_seconds_int}s"
            # --- 3. Open in a new browser tab ---
            webbrowser.open_new_tab(video_with_time)
        else:
            print("❌ Could not parse timestamp")
        




