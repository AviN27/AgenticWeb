"""Stream laptop microphone to Kafka as an EventEnvelope."""
import os, sys, json, uuid, time, asyncio, base64
import sounddevice as sd
import numpy as np
from aiokafka import AIOKafkaProducer

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
TOPIC      = os.getenv("VOICE_TOPIC_IN", "inbox")
RATE       = 16000
CHUNK      = 1024

async def main():
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP)
    await producer.start()

    print(f"[mic_client] Using bootstrap: {os.getenv('KAFKA_BOOTSTRAP')}")
    print("[mic_client] Press Enter to start recording…")
    
    input()
    trace_id = str(uuid.uuid4())
    user_id  = "demo-user"

    rec = sd.rec(int(RATE*30), samplerate=RATE, channels=1, dtype='int16')  # 30‑s max
    t0 = time.time()
    input()  # wait for second Enter
    sd.stop()
    pcm_bytes = rec.tobytes()[:int((time.time()-t0)*RATE*2)]  # trim to actual time

    envelope = {
        "trace_id": trace_id,
        "user_id": user_id,
        "ts_epoch_ms": int(time.time()*1000),
        "payload": {
            "raw_audio": True,
            "audio_b64": base64.b64encode(pcm_bytes).decode()
        }
    }
    await producer.send_and_wait(TOPIC, json.dumps(envelope).encode())

    print(f"[mic_client] Sending {len(pcm_bytes)} bytes to topic {TOPIC}")
    await producer.stop()
    print()
    print("Sent", len(pcm_bytes)//2, "samples to Kafka →", TOPIC)

if __name__ == "__main__":
    asyncio.run(main())