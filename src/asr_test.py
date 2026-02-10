import argparse, wave, time
import riva.client
import riva.client.audio_io

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="localhost:50051")
    ap.add_argument("--wav", required=True, help="16kHz mono LINEAR16 wav")
    ap.add_argument("--lang", default="en-US")
    args = ap.parse_args()

    auth = riva.client.Auth(uri=args.server)
    asr = riva.client.ASRService(auth)

    # Streaming config: low-latency, no punctuation unless you enabled NLP service.
    config = riva.client.StreamingRecognitionConfig(
        config=riva.client.RecognitionConfig(
            encoding=riva.client.AudioEncoding.LINEAR_PCM,
            sample_rate_hertz=16000,
            language_code=args.lang,
            max_alternatives=1,
            enable_automatic_punctuation=False,
            verbatim_transcripts=True,
        ),
        interim_results=True,
    )

    with wave.open(args.wav, "rb") as wf:
        assert wf.getnchannels() == 1, "wav must be mono"
        assert wf.getframerate() == 16000, "wav must be 16kHz"
        sampwidth = wf.getsampwidth()
        assert sampwidth == 2, "wav must be 16-bit PCM"

        # chunk ~100ms
        chunk_frames = int(0.1 * wf.getframerate())
        
        def audio_generator():
            while True:
                data = wf.readframes(chunk_frames)
                if not data:
                    break
                yield data

        t0 = time.time()
        responses = asr.streaming_response_generator(audio_generator(), config)

        final_text = None
        for resp in responses:
            for result in resp.results:
                if result.is_final:
                    final_text = result.alternatives[0].transcript.strip()
                    print("\nFINAL:", final_text)
                else:
                    partial = result.alternatives[0].transcript.strip()
                    if partial:
                        print("\rPARTIAL: " + partial[:120], end="", flush=True)

        print("\nElapsed: %.2fs" % (time.time() - t0))

if __name__ == "__main__":
    main()
