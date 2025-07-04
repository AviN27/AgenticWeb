// src/hooks/useSpeech.ts
import { useState, useEffect, useCallback } from 'react';
import { AudioModule, useAudioRecorder, RecordingPresets } from 'expo-audio';
import { Alert } from 'react-native';

export default function useSpeech() {
  const [transcript, setTranscript] = useState('');
  const [listening, setListening] = useState(false);
  const audioRecorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);

  // ask for permission once
  useEffect(() => {
    (async () => {
      const { granted } = await AudioModule.requestRecordingPermissionsAsync();
      if (!granted) {
        Alert.alert('Permission to access microphone was denied');
      }
    })();
  }, []);

  const record = async () => {
    await audioRecorder.prepareToRecordAsync();
    audioRecorder.record();
    setListening(true);
  };


  const stop = useCallback(async () => {
    try {
      await audioRecorder.stop();
      setListening(false);

      const uri = audioRecorder.uri;
      if (!uri) return;

      // send to backend ASR
      const form = new FormData();
      form.append('file', {
        uri,
        name: 'speech.wav',
        type: 'audio/wav',
      } as any);

      const res = await fetch(`${process.env.BACKEND_BASE_URL}/v1/asr`, {
        method: 'POST',
        body: form,
      });
      const json = await res.json();
      setTranscript(json.transcript ?? '');
    } catch (err) {
      console.error('stop recording error', err);
    }
  }, [audioRecorder]);

  return { transcript, listening, record, stop };
}