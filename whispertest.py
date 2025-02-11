import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wavfile
import tempfile
import os
from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
import torch

# Load model and processor directly from Hugging Face Transformers
processor = AutoProcessor.from_pretrained("openai/whisper-large-v3-turbo")
model = AutoModelForSpeechSeq2Seq.from_pretrained("openai/whisper-large-v3-turbo")

# Check if CUDA is available and move model to GPU if possible
device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)

def record_audio(duration=10, fs=16000):
    """Records audio from the microphone for a given duration."""
    print("Recording for up to 10 seconds...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32')
    sd.wait()  # Wait until recording is finished
    print("Finished recording.")
    return recording, fs

def transcribe_audio_local_whisper_large_turbo(audio_data, sample_rate):
    """Transcribes audio data locally using whisper-large-v3-turbo model."""

    print("Transcribing locally using whisper-large-v3-turbo...")

    # Convert audio data to expected format and sample rate
    audio_input = audio_data.flatten() # Flatten to mono if it's not already
    input_features = processor(audio_input, sampling_rate=sample_rate, return_tensors="pt").input_features

    # Move input features to the same device as the model (GPU if available)
    input_features = input_features.to(device)

    # Generate token ids
    predicted_ids = model.generate(input_features)

    # Decode token ids to text
    transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
    text = transcription

    return text

if __name__ == "__main__":
    recording, sample_rate = record_audio(duration=10) # Record for up to 10 seconds
    transcribed_text = transcribe_audio_local_whisper_large_turbo(recording, sample_rate)

    print("\nTranscription (Local whisper-large-v3-turbo - Terminal Output):")
    print(transcribed_text)
    print("\n--- End of Transcription ---")