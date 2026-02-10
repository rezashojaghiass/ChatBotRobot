#!/usr/bin/env python3
"""
Real-time voice chat using Riva ASR + TTS + AWS Bedrock LLM
Records from microphone, transcribes with Riva ASR, queries AWS Bedrock, speaks response with Riva TTS

Modes:
- chat: Regular conversation with Buzz Lightyear
- madagascar_quiz: Buzz Lightyear asks Madagascar movie questions
"""

import argparse
import io
import json
import time
import random
import wave
import os
import re
import numpy as np
from datetime import datetime
import pyaudio
import riva.client
import boto3
from botocore.exceptions import ClientError
from ctypes import *

# Madagascar facts pack (hardcoded for quiz mode)
MADAGASCAR_FACTS = """Madagascar core facts (allowed facts):
- Alex is a lion
- Marty is a zebra
- Gloria is a hippo
- Melman is a giraffe
- Penguins: Skipper, Kowalski, Rico, Private
- King Julien is a lemur
- They start at the Central Park Zoo and end up in Madagascar"""

# Global RAG storage
RAG_CHUNKS = []
RAG_EMBEDDINGS = None
RAG_MODEL = None

def load_srt_file(filepath):
    """Load and parse SRT subtitle file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse SRT format: remove timestamps and numbers
        lines = content.split('\n')
        dialogues = []
        current_dialogue = []
        
        for line in lines:
            line = line.strip()
            # Skip subtitle numbers and timestamps
            if line.isdigit() or '-->' in line or not line:
                if current_dialogue:
                    dialogues.append(' '.join(current_dialogue))
                    current_dialogue = []
            else:
                current_dialogue.append(line)
        
        # Add last dialogue
        if current_dialogue:
            dialogues.append(' '.join(current_dialogue))
        
        return dialogues
    except Exception as e:
        print(f"❌ Failed to load subtitle file: {e}")
        return []

def chunk_dialogues(dialogues, chunk_size=10):
    """Group dialogues into chunks for better context"""
    chunks = []
    for i in range(0, len(dialogues), chunk_size):
        chunk = ' '.join(dialogues[i:i+chunk_size])
        if len(chunk) > 50:  # Skip very short chunks
            chunks.append(chunk)
    return chunks

def initialize_rag(subtitle_path, use_local=True):
    """Initialize RAG system with subtitle content"""
    global RAG_CHUNKS, RAG_EMBEDDINGS, RAG_MODEL
    
    print(f"🔧 Initializing RAG with {subtitle_path}...")
    
    # Load subtitles
    dialogues = load_srt_file(subtitle_path)
    if not dialogues:
        print("⚠️  No dialogues loaded, using basic facts only")
        return False
    
    print(f"📝 Loaded {len(dialogues)} dialogues")
    
    # Chunk dialogues
    RAG_CHUNKS = chunk_dialogues(dialogues, chunk_size=10)
    print(f"📦 Created {len(RAG_CHUNKS)} chunks")
    
    # Generate embeddings
    if use_local:
        try:
            from sentence_transformers import SentenceTransformer
            print("🔄 Loading embedding model (this may take a moment)...")
            RAG_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
            print("🔄 Generating embeddings...")
            RAG_EMBEDDINGS = RAG_MODEL.encode(RAG_CHUNKS, show_progress_bar=False)
            print(f"✅ RAG initialized with {len(RAG_CHUNKS)} chunks")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize RAG: {e}")
            return False
    
    return False

def get_relevant_context(query, top_k=3):
    """Retrieve most relevant chunks for a query"""
    global RAG_CHUNKS, RAG_EMBEDDINGS, RAG_MODEL
    
    if not RAG_CHUNKS or RAG_EMBEDDINGS is None or RAG_MODEL is None:
        return MADAGASCAR_FACTS  # Fallback to basic facts
    
    try:
        # Encode query
        query_embedding = RAG_MODEL.encode([query])[0]
        
        # Calculate cosine similarity
        similarities = np.dot(RAG_EMBEDDINGS, query_embedding) / (
            np.linalg.norm(RAG_EMBEDDINGS, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # Get top K indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        # Return relevant chunks
        context_parts = [RAG_CHUNKS[i] for i in top_indices if similarities[i] > 0.2]
        
        if context_parts:
            return "\n".join(context_parts[:top_k])
        else:
            return MADAGASCAR_FACTS
    except Exception as e:
        print(f"⚠️  RAG retrieval failed: {e}")
        return MADAGASCAR_FACTS

# Suppress ALSA warnings
ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
def py_error_handler(filename, line, function, err, fmt):
    pass
c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
try:
    asound = cdll.LoadLibrary('libasound.so.2')
    asound.snd_lib_error_set_handler(c_error_handler)
except:
    pass  # If suppression fails, continue anyway

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

def record_audio_vad(max_duration=10, rate=16000, device_index=None, silence_threshold=500, silence_duration=0.5):
    """Record audio with voice activity detection (stops when user stops speaking)"""
    import struct
    import math
    
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
    
    print(f"🎤 Recording (will auto-stop after {silence_duration:.1f}s silence, max {max_duration}s)...")
    frames = []
    silence_frames = 0
    silence_threshold_frames = int(silence_duration * hw_rate / 1024)
    has_speech = False
    
    for i in range(0, int(hw_rate / 1024 * max_duration)):
        data = stream.read(1024, exception_on_overflow=False)
        frames.append(data)
        
        # Calculate RMS energy to detect speech
        rms = 0
        count = len(data) // 2
        format = "%dh" % count
        shorts = struct.unpack(format, data)
        sum_squares = sum([s**2 for s in shorts])
        rms = math.sqrt(sum_squares / count)
        
        # Track speech and silence
        if rms > silence_threshold:
            silence_frames = 0
            has_speech = True
        else:
            if has_speech:  # Only count silence after we've detected speech
                silence_frames += 1
        
        # Stop if we've detected speech and then silence
        if has_speech and silence_frames > silence_threshold_frames:
            print("✓ Silence detected, stopping...")
            break
    
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
def invoke_with_backoff(client, **kwargs):
    """Invoke Bedrock with exponential backoff for throttling"""
    base = 0.4   # seconds
    cap  = 8.0   # seconds
    for attempt in range(10):
        try:
            return client.invoke_model(**kwargs)
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code in ("ThrottlingException", "TooManyRequestsException"):
                sleep = min(cap, base * (2 ** attempt)) * (1 + random.random() * 0.3)
                print(f"⏳ Throttled, sleeping {sleep:.1f}s (attempt {attempt+1}/10)")
                time.sleep(sleep)
                continue
            raise
    raise RuntimeError("Bedrock throttling: exceeded retry budget")

# Track last LLM call time
last_llm_call = 0.0

def query_aws_bedrock(text, model_id="meta.llama3-8b-instruct-v1:0", region="us-east-1"):
    """Query AWS Bedrock LLM with throttling protection"""
    global last_llm_call
    
    # Guard: minimum text length
    if len(text.strip()) < 8:
        print("⚠️  Text too short, skipping LLM")
        return "Could you say that again?"
    
    # Guard: minimum time since last call (Claude needs more cooldown)
    cooldown = 3.0 if "claude" in model_id else 1.5
    elapsed = time.time() - last_llm_call
    if elapsed < cooldown:
        time.sleep(cooldown - elapsed)
    
    print("🤔 Thinking (AWS Bedrock)...")
    last_llm_call = time.time()
    
    try:
        bedrock = boto3.client('bedrock-runtime', region_name=region)
        
        # System context: Buzz Lightyear personality
        system_prompt = """You are Buzz Lightyear, the Space Ranger toy, speaking to Adrian.
You are brave, heroic, and sometimes overly serious about your space ranger duties.
Use phrases like "To infinity and beyond!", "Space Ranger reporting for duty", and similar Buzz Lightyear expressions.
Keep responses short (1-2 sentences) and stay in character.
You believe you're a real space ranger protecting Adrian."""
        
        # Format based on model type
        if "claude" in model_id:
            # Claude format
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 200,
                "temperature": 0.7,
                "system": system_prompt,
                "messages": [
                    {"role": "user", "content": f"Adrian: {text}"}
                ]
            })
        else:
            # Llama format
            body = json.dumps({
                "prompt": f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\nAdrian: {text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\nBuzz Lightyear: ",
                "max_gen_len": 200,
                "temperature": 0.7,
                "stop": ["<|eot_id|>", "Adrian:", "\nAdrian:", "\n\n"]
            })
        
        response = invoke_with_backoff(
            bedrock,
            modelId=model_id,
            body=body,
            contentType="application/json",
            accept="application/json"
        )
        
        response_body = json.loads(response['body'].read())
        
        # Extract text based on model type
        if "claude" in model_id:
            raw_text = response_body['content'][0]['text'].strip()
        else:
            raw_text = response_body['generation'].strip()
        
        # Clean up: take only first response, remove any continuation
        response_text = raw_text.split('Adrian:')[0].strip()
        
        print(f"💬 Buzz: {response_text}")
        return response_text
        
    except Exception as e:
        print(f"❌ AWS Bedrock error: {e}")
        return "I'm having trouble connecting to AWS right now."

def query_bedrock_json(system_prompt, user_input, model_id="meta.llama3-8b-instruct-v1:0", region="us-east-1"):
    """Query AWS Bedrock and expect JSON response (for quiz mode)"""
    global last_llm_call
    
    # Guard: minimum time since last call (Claude needs more cooldown)
    cooldown = 3.0 if "claude" in model_id else 1.5
    elapsed = time.time() - last_llm_call
    if elapsed < cooldown:
        time.sleep(cooldown - elapsed)
    
    last_llm_call = time.time()
    
    try:
        bedrock = boto3.client('bedrock-runtime', region_name=region)
        
        # Format based on model type
        if "claude" in model_id:
            # Claude format
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 400,
                "temperature": 0.7,
                "system": system_prompt,
                "messages": [
                    {"role": "user", "content": user_input}
                ]
            })
        else:
            # Llama format
            body = json.dumps({
                "prompt": f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{user_input}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
                "max_gen_len": 400,
                "temperature": 0.7,
                "stop": ["<|eot_id|>", "\n\n\n"]
            })
        
        response = invoke_with_backoff(
            bedrock,
            modelId=model_id,
            body=body,
            contentType="application/json",
            accept="application/json"
        )
        
        response_body = json.loads(response['body'].read())
        
        # Extract text based on model type
        if "claude" in model_id:
            raw_text = response_body['content'][0]['text'].strip()
        else:
            raw_text = response_body['generation'].strip()
        
        return raw_text
        
    except Exception as e:
        print(f"❌ AWS Bedrock error: {e}")
        return None

def quiz_tutor_call(kid_name, quiz_state, model_id="meta.llama3-8b-instruct-v1:0", region="us-east-1", use_rag=False, topic="the Madagascar movie"):
    """Buzz Lightyear asks next quiz question (returns JSON)\"\"\"
    print("🎓 Tutor: Generating question...")
    
    # Calculate difficulty based on progress
    progress = quiz_state['question_idx'] / quiz_state['max_questions']
    if progress < 0.3:
        difficulty = "easy"
        difficulty_instruction = "Ask a VERY EASY question suitable for young children (e.g., main character names, basic facts)."
    elif progress < 0.7:
        difficulty = "medium"
        difficulty_instruction = "Ask a MEDIUM difficulty question (e.g., character relationships, plot points)."
    else:
        difficulty = "hard"
        difficulty_instruction = "Ask a HARDER question (e.g., specific scenes, quotes, details)."
    
    # Get context (RAG or basic facts)
    if use_rag and RAG_CHUNKS:
        context = get_relevant_context(f"{topic} question {quiz_state['question_idx']}")
        context_label = "RAG context"
    else:
        context = MADAGASCAR_FACTS
        context_label = "facts"
    
    system_prompt = f"""You are Buzz Lightyear tutoring {kid_name} about {topic}.
You are ENTHUSIASTIC, ENCOURAGING, and EXCITED! Use phrases like "To infinity and beyond!", "Great job Space Ranger!", "Fantastic!".
Ask ONE question at a time about {topic}.
{difficulty_instruction}
Use ONLY these {context_label}: {context}
Keep it kid-friendly and fun.
Return ONLY valid JSON with no extra text.

Required JSON schema:
{{
  "say": "1-2 short ENTHUSIASTIC sentences in excited Buzz voice ending with a question",
  "question": "Question text",
  "expected": ["list", "of", "acceptable", "answers"],
  "difficulty": "{difficulty}"
}}

Example:
{{"say": "Alright Space Ranger {kid_name}, here's an easy one for you! What type of animal is Alex? To infinity and beyond!", "question": "What animal is Alex?", "expected": ["lion", "a lion", "the lion"], "difficulty": "{difficulty}"}}"""
    
    user_input = f"""Score: {quiz_state['score']}/{quiz_state['question_idx']}
Streak: {quiz_state['streak']}
History: {quiz_state['history_summary'] or 'Just starting'}

Generate next question (question #{quiz_state['question_idx'] + 1})."""
    
    raw_response = query_bedrock_json(system_prompt, user_input, model_id, region)
    
    if not raw_response:
        return None
    
    # Try to parse JSON
    try:
        # Try to extract JSON if there's extra text
        json_start = raw_response.find('{')
        json_end = raw_response.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_text = raw_response[json_start:json_end]
            result = json.loads(json_text)
            print(f"✓ Question generated: {result.get('question', 'N/A')}")
            return result
        else:
            raise ValueError("No JSON found in response")
    except Exception as e:
        print(f"❌ JSON parse error: {e}")
        print(f"Raw response: {raw_response[:200]}")
        return None

def quiz_judge_call(user_answer, expected_answers, last_question="", model_id="meta.llama3-8b-instruct-v1:0", region="us-east-1", use_rag=False, topic="the Madagascar movie"):
    """Grade user's answer (returns JSON with is_correct, feedback, etc.)"""
    print("⚖️  Judge: Grading answer...")
    
    # Get context (RAG or basic facts)
    if use_rag and RAG_CHUNKS:
        context = get_relevant_context(f"{last_question} {user_answer}")
        context_label = "RAG context"
    else:
        context = MADAGASCAR_FACTS
        context_label = "facts"
    
    system_prompt = f"""You are a kind, encouraging quiz grader for young children.
Be GENEROUS and LENIENT - if the answer is close or partially correct, mark it as CORRECT.
Accept synonyms, partial answers, and reasonable interpretations.
Use ONLY these {context_label} to judge: {context}
Be enthusiastic like Buzz Lightyear! Use phrases like "Bravo!", "Excellent work!", "Outstanding!", "Good job {user_answer.split()[0] if user_answer else 'Space Ranger'}!".
Decide if the answer is correct or incorrect based on the expected answers.
Be strict but fair. If answer is close/partial, still mark as correct but lower confidence.
Return ONLY valid JSON with no extra text.

Required JSON schema:
{{
  "is_correct": true or false,
  "normalized_answer": "cleaned answer",
  "confidence": 0.0 to 1.0,
  "short_feedback": "ENTHUSIASTIC and encouraging feedback (Bravo! Excellent! Good job!)",
  "hint_if_wrong": "gentle hint or empty string"
}}

Examples:
Correct answer: {{"is_correct": true, "normalized_answer": "lion", "confidence": 0.9, "short_feedback": "Bravo Adrian! That's absolutely correct! You're a real Space Ranger!", "hint_if_wrong": ""}}
Close answer: {{"is_correct": true, "normalized_answer": "big cat", "confidence": 0.7, "short_feedback": "Good job Adrian! Yes, Alex is a big cat - a lion! Excellent work!", "hint_if_wrong": ""}}
Wrong answer: {{"is_correct": false, "normalized_answer": "zebra", "confidence": 0.0, "short_feedback": "Not quite Space Ranger, but nice try!", "hint_if_wrong": "Think about the character who lives in the zoo and loves to perform. He's the king of the jungle!"}}"""
    
    user_input = f"""User answered: "{user_answer}"
Expected answers: {json.dumps(expected_answers)}

Grade the answer."""
    
    raw_response = query_bedrock_json(system_prompt, user_input, model_id, region)
    
    if not raw_response:
        return None
    
    # Try to parse JSON
    try:
        json_start = raw_response.find('{')
        json_end = raw_response.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_text = raw_response[json_start:json_end]
            result = json.loads(json_text)
            print(f"✓ Graded: {'Correct' if result.get('is_correct') else 'Incorrect'}")
            return result
        else:
            raise ValueError("No JSON found in response")
    except Exception as e:
        print(f"❌ JSON parse error: {e}")
        print(f"Raw response: {raw_response[:200]}")
        return None

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
    parser = argparse.ArgumentParser(description="Voice chat with Riva + AWS Bedrock")
    parser.add_argument("--server", default="localhost:50051", help="Riva server address")
    parser.add_argument("--model", default="meta.llama3-8b-instruct-v1:0", 
                        help="AWS Bedrock model ID")
    parser.add_argument("--llm", default="llama", choices=["llama", "llama70b", "claude"],
                        help="LLM provider: llama (8B, default), llama70b (70B), or claude")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--duration", type=int, default=5, help="Recording duration in seconds")
    parser.add_argument("--no-vad", action="store_true", help="Disable voice activity detection (use fixed duration)")
    parser.add_argument("--device", type=int, default=None, help="Audio input device index")
    parser.add_argument("--mode", default="chat", choices=["chat", "madagascar_quiz"],
                        help="Mode: chat or madagascar_quiz")
    parser.add_argument("--kid_name", default="Adrian", help="Kid's name for quiz mode")
    parser.add_argument("--quiz_len", type=int, default=10, help="Number of quiz questions")
    parser.add_argument("--rag", action="store_true", help="Enable RAG with subtitle file")
    parser.add_argument("--subtitle", default="/mnt/nvme/adrian/riva/Madagascar.720p.CHD.en.srt",
                        help="Path to subtitle file for RAG")
    parser.add_argument("--topic", default="the Madagascar movie",
                        help="Quiz topic (e.g., 'space and galaxies', 'Toy Story movie', etc.)")
    args = parser.parse_args()
    
    # Map LLM provider to model ID
    if args.llm == "claude":
        args.model = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"  # inference profile ID
    elif args.llm == "llama70b":
        args.model = "us.meta.llama3-1-70b-instruct-v1:0"  # inference profile ID
    elif args.llm == "llama":
        args.model = "meta.llama3-8b-instruct-v1:0"
    
    # Initialize RAG if requested
    if args.rag and args.mode == "madagascar_quiz":
        initialize_rag(args.subtitle)
    
    print("🤖 Riva + AWS Bedrock Voice Chat Ready!")
    print(f"📡 Using LLM: {args.llm.upper()}")
    print(f"📡 Model: {args.model}")
    print(f"🎯 Mode: {args.mode}")
    print(f"🎤 VAD: {'Disabled (fixed duration)' if args.no_vad else 'Enabled (auto-stop)'}")
    if args.mode == "madagascar_quiz":
        print(f"👤 Kid name: {args.kid_name}")
        print(f"❓ Quiz length: {args.quiz_len} questions")
        print(f"📚 RAG: {'Enabled (using subtitles)' if args.rag and RAG_CHUNKS else 'Disabled (using basic facts)'}")
    print("Press Ctrl+C to exit\n")
    
    if args.mode == "madagascar_quiz":
        run_quiz_mode(args)
    else:
        run_chat_mode(args)

def run_chat_mode(args):
    """Original chat mode"""
    try:
        while True:
            # Record (VAD enabled by default)
            if not args.no_vad:
                audio = record_audio_vad(max_duration=args.duration * 2, device_index=args.device)
            else:
                audio = record_audio(duration=args.duration, device_index=args.device)
            
            # Transcribe
            text = transcribe_riva(audio, server=args.server)
            if not text:
                print("❌ No speech detected, try again\n")
                continue
            
            # Query AWS Bedrock
            response = query_aws_bedrock(text, model_id=args.model, region=args.region)
            
            # Speak
            speak_riva(response, server=args.server)
            
            print("\n" + "="*60 + "\n")
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")

def run_quiz_mode(args):
    """Quiz mode with Buzz Lightyear on any topic"""
    
    # Initialize quiz state
    quiz_state = {
        "score": 0,
        "streak": 0,
        "question_idx": 0,
        "max_questions": args.quiz_len,
        "last_question": "",
        "last_expected": [],
        "history_summary": ""
    }
    
    # Introduction
    intro = f"Space Ranger {args.kid_name}, ready for a mission about {args.topic}? I'll quiz you! To infinity and beyond!"
    print(f"🎬 Quiz starting...")
    speak_riva(intro, server=args.server)
    
    try:
        while quiz_state["question_idx"] < quiz_state["max_questions"]:
            print(f"\n{'='*60}")
            print(f"Question {quiz_state['question_idx'] + 1}/{quiz_state['max_questions']}")
            print(f"Score: {quiz_state['score']} | Streak: {quiz_state['streak']}")
            print('='*60 + '\n')
            
            # Step 1: Tutor asks question
            tutor_result = quiz_tutor_call(args.kid_name, quiz_state, args.model, args.region, use_rag=args.rag, topic=args.topic)
            
            if not tutor_result:
                # Retry once
                print("⚠️  Retrying question generation...")
                time.sleep(1)
                tutor_result = quiz_tutor_call(args.kid_name, quiz_state, args.model, args.region, use_rag=args.rag, topic=args.topic)
                
            if not tutor_result or 'say' not in tutor_result or 'expected' not in tutor_result:
                print("❌ Failed to generate question, skipping...")
                speak_riva("Oops! Let's try that again!", server=args.server)
                continue
            
            # Store question and expected answers
            quiz_state["last_question"] = tutor_result.get("question", "")
            quiz_state["last_expected"] = tutor_result.get("expected", [])
            
            # Speak the question
            speak_riva(tutor_result["say"], server=args.server)
            
            # Step 2: Record and transcribe user's answer (VAD enabled by default)
            if not args.no_vad:
                audio = record_audio_vad(max_duration=args.duration * 2, device_index=args.device)
            else:
                audio = record_audio(duration=args.duration, device_index=args.device)
            user_answer = transcribe_riva(audio, server=args.server)
            
            # Guard: empty or too short
            if not user_answer or len(user_answer.strip()) < 3:
                speak_riva("I didn't catch that, say it again!", server=args.server)
                continue
            
            # Guard: exit intent
            exit_words = ["stop", "quit", "exit", "done", "finish"]
            if any(word in user_answer.lower() for word in exit_words):
                print("🛑 Exit intent detected")
                break
            
            # Step 3: Judge grades answer
            judge_result = quiz_judge_call(
                user_answer, 
                quiz_state["last_expected"], 
                quiz_state["last_question"],
                args.model, 
                args.region,
                use_rag=args.rag,
                topic=args.topic
            )
            
            if not judge_result:
                # Retry once
                print("⚠️  Retrying grading...")
                time.sleep(1)
                judge_result = quiz_judge_call(
                    user_answer,
                    quiz_state["last_expected"],
                    quiz_state["last_question"],
                    args.model,
                    args.region,
                    use_rag=args.rag,
                    topic=args.topic
                )
            
            if not judge_result or 'is_correct' not in judge_result:
                print("❌ Failed to grade, skipping...")
                speak_riva("Hmm, let me think about that one...", server=args.server)
                continue
            
            # Step 4: Process result and give feedback
            is_correct = judge_result.get("is_correct", False)
            feedback = judge_result.get("short_feedback", "")
            hint = judge_result.get("hint_if_wrong", "")
            
            if is_correct:
                quiz_state["score"] += 1
                quiz_state["streak"] += 1
                speak_riva(feedback, server=args.server)
            else:
                quiz_state["streak"] = 0
                full_feedback = f"{feedback} {hint}".strip()
                speak_riva(full_feedback, server=args.server)
            
            # Update history summary (keep it short)
            summary_entry = f"Q: {quiz_state['last_question'][:30]}... A: {user_answer[:20]} ({'✓' if is_correct else '✗'}). "
            quiz_state["history_summary"] = (quiz_state["history_summary"] + summary_entry)[-300:]
            
            # Increment question counter
            quiz_state["question_idx"] += 1
        
        # Quiz complete
        print(f"\n{'='*60}")
        print("🎉 Quiz Complete!")
        print(f"Final Score: {quiz_state['score']}/{quiz_state['max_questions']}")
        print('='*60 + '\n')
        
        wrap_up = f"Great job {args.kid_name}! You got {quiz_state['score']} out of {quiz_state['max_questions']} questions correct! To infinity and beyond!"
        speak_riva(wrap_up, server=args.server)
        
    except KeyboardInterrupt:
        print("\n\n👋 Quiz ended early!")
        print(f"Score: {quiz_state['score']}/{quiz_state['question_idx']}")

if __name__ == "__main__":
    main()
