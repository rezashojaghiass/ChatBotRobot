#!/usr/bin/env python3
"""
Simple speech-to-text test using RIVA ASR to verify microphone is working
Uses arecord to directly access RODE microphone on hw:2,0
"""

import sys
import subprocess
import riva.client
import os

def record_audio_arecord(duration=5):
    """Record audio using arecord directly from hw:2,0"""
    print(f"\n🎤 Recording from hw:2,0 for {duration} seconds...")
    print("   (Speak clearly into the microphone)")
    
    output_file = "/tmp/test_mic_recording.wav"
    
    cmd = [
        'arecord',
        '-D', 'hw:2,0',      # RODE Wireless GO II device
        '-f', 'S16_LE',      # 16-bit signed
        '-r', '48000',       # 48kHz (RODE native)
        '-c', '2',           # Stereo
        '-d', str(duration), # Duration
        output_file
    ]
    
    try:
        # Run arecord
        subprocess.run(cmd, check=True, capture_output=True)
        print("✅ Recording complete")
        
        # Read the file
        with open(output_file, 'rb') as f:
            audio_data = f.read()
        
        # Convert WAV to raw audio (skip WAV header - 44 bytes)
        raw_audio = audio_data[44:]
        
        # Resample from 48kHz to 16kHz using sox if available
        try:
            output_16k = "/tmp/test_mic_16k.wav"
            sox_cmd = [
                'sox',
                output_file,
                '-r', '16000',
                output_16k
            ]
            subprocess.run(sox_cmd, check=True, capture_output=True)
            
            # Read 16kHz file
            with open(output_16k, 'rb') as f:
                audio_16k_wav = f.read()
            raw_audio = audio_16k_wav[44:]
        except Exception as e:
            print(f"⚠️  sox not available, using audioop for resampling: {e}")
            import audioop
            raw_audio, _ = audioop.ratecv(raw_audio, 2, 2, 48000, 16000, None)
        
        return raw_audio
    except Exception as e:
        print(f"❌ Recording error: {e}")
        return None

def transcribe_with_riva(audio_bytes):
    """Send audio to RIVA ASR server and get transcription"""
    try:
        print("\n🚀 Connecting to Riva ASR at localhost:50051...")
        auth = riva.client.Auth(uri='localhost:50051')
        asr_service = riva.client.ASRService(auth)
        
        print("📤 Sending audio to Riva ASR...")
        
        # Prepare config
        config = riva.client.StreamingRecognitionConfig(
            config=riva.client.RecognitionConfig(
                encoding=riva.client.AudioEncoding.LINEAR_PCM,
                sample_rate_hertz=16000,
                language_code="en-US",
                max_alternatives=1,
            ),
            interim_results=False,
        )
        
        # Stream audio
        def audio_chunks():
            chunk_size = 1600  # 100ms at 16kHz
            for i in range(0, len(audio_bytes), chunk_size):
                yield audio_bytes[i:i+chunk_size]
        
        transcription = ""
        confidence = 0.0
        
        responses = asr_service.streaming_response_generator(audio_chunks(), config)
        for response in responses:
            if response.results:
                result = response.results[0]
                if result.is_final:
                    transcription = result.alternatives[0].transcript
                    confidence = result.alternatives[0].confidence
        
        if not transcription:
            transcription = "(no speech detected)"
        
        return transcription, confidence
    except Exception as e:
        print(f"❌ Riva error: {e}")
        import traceback
        traceback.print_exc()
        return None, 0.0

def main():
    print("=" * 60)
    print("RIVA Speech-to-Text Microphone Test")
    print("=" * 60)
    
    # Record audio using arecord
    audio_bytes = record_audio_arecord(duration=5)
    
    if audio_bytes is None:
        print("\n❌ Failed to record audio. Check microphone connection.")
        sys.exit(1)
    
    # Send to Riva ASR
    transcription, confidence = transcribe_with_riva(audio_bytes)
    
    if transcription is None:
        print("\n❌ Failed to connect to Riva ASR.")
        print("   Make sure Riva is running: docker ps | grep riva")
        sys.exit(1)
    
    # Display results
    print("\n" + "=" * 60)
    print("RESULTS:")
    print("=" * 60)
    print(f"📝 Transcription: {transcription}")
    print(f"🎯 Confidence: {confidence * 100:.1f}%")
    print("=" * 60)
    
    if transcription == "(no speech detected)":
        print("\n⚠️  No speech detected. Check:")
        print("   1. Microphone is plugged in and turned on")
        print("   2. Microphone volume is not too low")
        print("   3. You spoke clearly during recording")
        sys.exit(1)
    else:
        print("\n✅ Microphone and Riva ASR working correctly!")
        sys.exit(0)

if __name__ == "__main__":
    main()
