import os, json, wave, tempfile, time, uuid, asyncio, logging
import base64
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from faster_whisper import WhisperModel

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("v2p")

os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"
BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092").split(",")
IN_TOPIC  = os.getenv("VOICE_TOPIC_IN",  "inbox")
OUT_TOPIC = os.getenv("VOICE_TOPIC_OUT", "transcript")

model = WhisperModel("medium", device="cpu", compute_type="int8")

async def transcribe_loop():
    consumer = AIOKafkaConsumer(
        IN_TOPIC,
        bootstrap_servers=BOOTSTRAP,
        group_id="voice_to_prompt",
        auto_offset_reset="earliest"
    )

    await consumer.start()

    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP)
    await producer.start()
    log.debug(f"CONSUMER: {consumer}, PRODUCER: {producer}")

    try:
        async for msg in consumer:
            try:
                envelope = json.loads(msg.value.decode())
                log.debug(f"[v2p] Received envelope: keys={list(envelope.keys())}")

                audio_b64 = envelope["payload"].get("audio_b64","")
                pcm_bytes = base64.b64decode(audio_b64)
                log.debug(f"[v2p] Decoded {len(pcm_bytes)} bytes (base64)")

                # Write a valid WAV file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    wav_path = tmp.name
                with wave.open(wav_path, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(16000)
                    wf.writeframes(pcm_bytes)
                log.debug(f"[v2p] Wrote WAV to {wav_path}")

                # Transcribe
                segments, _ = model.transcribe(wav_path, beam_size=5)
                text = " ".join(seg.text.strip() for seg in segments if seg.text.strip())
                log.info(f"[v2p] Transcribed: {text!r}")

                out_msg = {
                    "trace_id":   envelope.get("trace_id"),
                    "user_id":    envelope.get("user_id"),
                    "text":       text,
                    "ts_epoch_ms":int(time.time()*1000)
                }
                await producer.send_and_wait(OUT_TOPIC, json.dumps(out_msg).encode())
                log.debug(f"[v2p] Published to {OUT_TOPIC}: {out_msg}")

            except Exception as e:
                log.error(f"[v2p] Processing error: {e}", exc_info=True)

    finally:
        log.info("[v2p] Stopping consumer & producer")
        await consumer.stop()
        await producer.stop()

if __name__ == "__main__":
    asyncio.run(transcribe_loop())