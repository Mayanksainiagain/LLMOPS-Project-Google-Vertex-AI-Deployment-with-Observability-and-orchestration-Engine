"""
Google Cloud Video Processing Service.
Replaces Azure Video Indexer with TWO specialized APIs:
  - Google Cloud Storage (file upload)
  - Google Cloud Speech-to-Text V2 + Chirp 3 (transcription) ← ACCURATE + CHEAP
  - Google Cloud Video Intelligence API (OCR / text detection) ← VISUAL TEXT
"""
import os
import logging
import subprocess
import yt_dlp
from google.cloud import storage
from google.cloud import videointelligence_v1 as vi
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech

logger = logging.getLogger("video-intelligence")


class VideoIntelligenceService:
    """
    Google Cloud equivalent of VideoIndexerService.

    Azure needed: 5 env vars + 2-step token exchange
    GCP needs: 1 env var (GCP_PROJECT_ID) + ADC auto-auth

    Architecture:
        Video → GCS → Speech-to-Text V2 (transcript — Chirp 3 model)
                    → Video Intelligence API (OCR — text on screen)
    """

    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.location = os.getenv("GCP_LOCATION", "us-central1")
        self.bucket_name = os.getenv("GCS_BUCKET_NAME")
        self.storage_client = storage.Client()
        self.video_client = vi.VideoIntelligenceServiceClient()
        self.speech_client = SpeechClient()

    # ========== STEP 1: DOWNLOAD (unchanged — yt-dlp is cloud-agnostic) ==========
    def download_youtube_video(self, url: str, output_path: str = "temp_video.mp4") -> str:
        """Downloads a YouTube video to a local file."""
        logger.info(f"Downloading YouTube video: {url}")
        ydl_opts = {
            'format': 'best',
            'outtmpl': output_path,
            'quiet': False,
            'no_warnings': False,
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            logger.info("Download complete.")
            return output_path
        except Exception as e:
            raise Exception(f"YouTube Download Failed: {str(e)}")

    # ========== STEP 2: UPLOAD TO GCS ==========
    def upload_to_gcs(self, local_path: str, blob_name: str) -> str:
        """
        Uploads local video file to Google Cloud Storage.

        Azure needed: ARM Token → Account Token → POST to API
        GCP needs: Just upload. ADC handles auth automatically.
        """
        logger.info(f"Uploading {local_path} to gs://{self.bucket_name}/{blob_name}")
        bucket = self.storage_client.bucket(self.bucket_name)
        blob = bucket.blob(f"videos/{blob_name}")
        blob.upload_from_filename(local_path)
        gcs_uri = f"gs://{self.bucket_name}/videos/{blob_name}"
        logger.info(f"Upload complete: {gcs_uri}")
        return gcs_uri

    # ========== STEP 3: EXTRACT AUDIO (needed for Speech-to-Text V2) ==========
    def extract_audio(self, video_path: str, audio_path: str = "temp_audio.wav") -> str:
        """
        Extracts audio track from video using ffmpeg.
        Speech-to-Text V2 works on audio files, not video files.
        The audio is saved as WAV (LINEAR16) for best compatibility.
        """
        logger.info(f"Extracting audio from {video_path}...")
        cmd = [
            "ffmpeg", "-i", video_path,
            "-vn",                    # No video
            "-acodec", "pcm_s16le",   # LINEAR16 encoding (best for Speech API)
            "-ar", "16000",           # 16kHz sample rate (optimal for speech)
            "-ac", "1",               # Mono channel
            "-y",                     # Overwrite output
            audio_path
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        logger.info(f"Audio extracted: {audio_path}")
        return audio_path

    # ========== STEP 4: TRANSCRIBE with Speech-to-Text V2 (Chirp 3) ==========
    def transcribe_audio(self, gcs_audio_uri: str) -> str:
        """
        Uses Google Cloud Speech-to-Text V2 with Chirp 3 model.

        """
        logger.info(f"Transcribing with Speech-to-Text V2 (Chirp 3): {gcs_audio_uri}")

        # Create a Recognizer resource (Speech V2 concept — reusable config)
        recognizer_name = f"projects/{self.project_id}/locations/{self.location}/recognizers/_"

        # Configure the recognition request
        config = cloud_speech.RecognitionConfig(
            auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
            language_codes=["en-US"],
            model="chirp_2",  # Chirp 3 model for best accuracy (use "chirp" for Chirp 1)
            features=cloud_speech.RecognitionFeatures(
            enable_automatic_punctuation=True,
            enable_word_time_offsets=True,  # Timestamps for each word
            ),
        )

        # Use BatchRecognize for long audio files (>1 min)
        file_metadata = cloud_speech.BatchRecognizeFileMetadata(uri=gcs_audio_uri)

        request = cloud_speech.BatchRecognizeRequest(
            recognizer=recognizer_name,
            config=config,
            files=[file_metadata],
            recognition_output_config=cloud_speech.RecognitionOutputConfig(
                inline_response_config=cloud_speech.InlineOutputConfig(),
            ),
        )

        # Submit batch job — GCP handles polling internally!
        logger.info("Waiting for transcription (may take a few minutes)...")
        operation = self.speech_client.batch_recognize(request=request)
        response = operation.result(timeout=600)

        # Extract transcript text from response
        transcript_parts = []
        for file_result in response.results.values():
            for result in file_result.transcript.results:
                for alternative in result.alternatives:
                    if alternative.transcript:
                        transcript_parts.append(alternative.transcript)

        transcript = " ".join(transcript_parts)
        logger.info(f"Transcription complete. Length: {len(transcript)} chars")
        return transcript

    # ========== STEP 5: OCR with Video Intelligence API ==========
    def detect_text_in_video(self, gcs_video_uri: str) -> list:
        """
        Uses Google Video Intelligence API for OCR (on-screen text detection).
        We ONLY use Video Intelligence for visual text, NOT for speech.
        """
        logger.info(f"Detecting on-screen text: {gcs_video_uri}")

        features = [vi.Feature.TEXT_DETECTION]  # OCR only, no speech!

        request = vi.AnnotateVideoRequest(
            input_uri=gcs_video_uri,
            features=features,
        )

        logger.info("Waiting for OCR processing...")
        operation = self.video_client.annotate_video(request=request)
        result = operation.result(timeout=600)

        ocr_lines = []
        for annotation_result in result.annotation_results:
            for text_annotation in getattr(annotation_result, 'text_annotations', []):
                if text_annotation.text:
                    ocr_lines.append(text_annotation.text)

        unique_ocr = list(set(ocr_lines))  # Deduplicate
        logger.info(f"OCR complete. Found {len(unique_ocr)} unique text segments.")
        return unique_ocr

    # ========== STEP 6: ORCHESTRATE ALL STEPS ==========
    def process_video(self, video_url: str, video_id: str) -> dict:
        """
        Full processing pipeline — called by the Indexer node.

        Flow:
        1. Download YouTube video
        2. Extract audio (for Speech V2)
        3. Upload video + audio to GCS
        4. Run Speech-to-Text V2 (transcript) + Video Intelligence (OCR) in parallel
        5. Return structured data for the graph state
        """
        local_video = "temp_audit_video.mp4"
        local_audio = "temp_audit_audio.wav"

        # 1. Download
        self.download_youtube_video(video_url, local_video)

        # 2. Extract audio for Speech V2
        self.extract_audio(local_video, local_audio)

        # 3. Upload both to GCS
        gcs_video_uri = self.upload_to_gcs(local_video, f"{video_id}.mp4")
        gcs_audio_uri = self.upload_to_gcs(local_audio, f"{video_id}.wav")

        # 4. Cleanup local files
        for f in [local_video, local_audio]:
            if os.path.exists(f):
                os.remove(f)

        # 5. Process (these could be parallelized with asyncio in production)
        transcript = self.transcribe_audio(gcs_audio_uri)
        ocr_text = self.detect_text_in_video(gcs_video_uri)

        # 6. Return structured result
        return {
            "transcript": transcript,
            "ocr_text": ocr_text,
            "video_metadata": {
                "platform": "youtube",
                "transcription_model": "chirp_2",
                "ocr_engine": "google-video-intelligence",
            }
        }
