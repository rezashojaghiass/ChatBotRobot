#!/usr/bin/env python3
"""
Real-time voice chat using Riva ASR + TTS + LLM
Records from microphone, transcribes with Riva ASR, queries LLM, speaks response with Riva TTS
"""

import argparse
import io
import wave
import requests
import pyaudio
import riva.client

def record_audio(duration=5, rate=16000, device_index=None):
    """Record audio from microphone"""
    p = pyaudio.PyAudio()
    
    # If no device specified, try to find Wireless GO II
    if device_index is None:
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if 'Wireless GO II' in info['name'] and info['maxInputChannels'] > 0:
                device_index = i
                print(f"✓ Found Wireless GO II on device {i}")
                break
    
    # Wireless GO II is 48kHz, need to resample to 16kHz
    hw_rate = 48000
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=hw_rate,
        input=True,
        input_device_index=device_index,
        frames_per_buffer=1024
    )
    
    print(f"🎤 Recording for {duration} seconds...")
    frames = []
    for _ in range(0, int(hw_rate / 1024 * duration)):
        data = stream.read(1024, exception_on_overflow=False)
        frames.append(data)
    
    print("✓ Recording complete")
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # Resample from 48kHz to 16kHz
    import audioop
    audio_48k = b''.join(frames)
    audio_16k, _ = audioop.ratecv(audio_48k, 2, 1, hw_rate, rate, None)
    
    return audio_16k

def transcribe_riva(audio_data, server="localhost:50051", rate=16000):
    """Transcribe audio using Riva ASR (streaming)"""
    print("🔄 Transcribing...")
    
    auth = riva.client.Auth(uri=server)
    asr = riva.client.ASRService(auth)
    
    config = riva.client.StreamingRecognitionConfig(
        config=riva.client.RecognitionConfig(
            encoding=riva.client.AudioEncoding.LINEAR_PCM,
            sample_rate_hertz=rate,
            language_code="en-US",
            max_alternatives=1,
            enable_automatic_punctuation=False,
        ),
        interim_results=False,
    )
    
    # Stream audio in chunks
    def audio_chunks():
        chunk_size = 1600  # 100ms at 16kHz
        for i in range(0, len(audio_data), chunk_size):
            yield audio_data[i:i+chunk_size]
    
    final_text = ""
    responses = asr.streaming_response_generator(audio_chunks(), config)
    
    for response in responses:
        for result in response.results:
            if result.is_final:
                final_text = result.alternatives[0].transcript.strip()
    
    if final_text:
        print(f"📝 You said: {final_text}")
        return final_text
    return ""

def query_llm(text, llm_url="http://127.0.0.1:8080/completion"):
    """Query LLM server"""
    print("🤔 Thinking...")
    
    payload = {
        "prompt": f"User: {text}\nAssistant:",
        "temperature": 0.7,
        "max_tokens": 150,
        "stop": ["\nUser:", "\n\n"]
    }
    
    try:
        resp = requests.post(llm_url, json=payload, timeout=30)
        resp.raise_for_status()
        response_text = resp.json().get("content", "").strip()
        print(f"💬 Response: {response_text}")
        return response_text
    except Exception as e:
        print(f"❌ LLM error: {e}")
        return "I'm having trouble thinking right now."

def speak_riva(text, server="localhost:50051", rate=22050):
    """Synthesize and play speech using Riva TTS"""
    print("🔊 Speaking...")
    
    auth = riva.client.Auth(uri=server)
    tts = riva.client.SpeechSynthesisService(auth)
    
    resp = tts.synthesize(
        text=text,
        language_code="en-US",
        encoding=riva.client.AudioEncoding.LINEAR_PCM,
        sample_rate_hz=rate,
        voice_name="English-US.Male-1"
    )
    
    audio_data = resp.audio
    
    # Play audio
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=rate, output=True)
    stream.write(audio_data)
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    print("✓ Done speaking")

def main():
    parser = argparse.ArgumentParser(description="Voice chat with Riva")
    parser.add_argument("--server", default="localhost:50051", help="Riva server address")
    parser.add_argument("--llm", default="http://127.0.0.1:8080/completion", help="LLM endpoint")
    parser.add_argument("--duration", type=int, default=5, help="Recording duration in seconds")
    parser.add_argument("--device", type=int, default=None, help="Audio input device index")
    args = parser.parse_args()
    
    print("🤖 Riva Voice Chat Ready!")
    print("Press Ctrl+C to exit\n")
    
    try:
        while True:
            # Record
            audio = record_audio(duration=args.duration, device_index=args.device)
            
            # Transcribe
            text = transcribe_riva(audio, server=args.server)
            if not text:
                print("❌ No speech detected, try again\n")
                continue
            
            # Query LLM
            response = query_llm(text, llm_url=args.llm)
            
            # Speak
            speak_riva(response, server=args.server)
            
            print("\n" + "="*60 + "\n")
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")

if __name__ == "__main__":
    main()
