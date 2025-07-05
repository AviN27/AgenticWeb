// src/hooks/useVoiceStream.ts
import { useState, useRef, useEffect, useCallback } from 'react';
import { Platform, Alert } from 'react-native';
import AudioRecord from 'react-native-audio-record';
import { request, PERMISSIONS, RESULTS } from 'react-native-permissions';

interface AudioRecordOptions {
  sampleRate: number;
  channels: number;
  bitsPerSample: number;
  wavFile: string;
}

interface VoiceStreamOpts {
  wsUrl: string;
}

export default function useVoiceStream({ wsUrl }: VoiceStreamOpts) {
  const wsRef = useRef<WebSocket | null>(null);
  const [listening, setListening] = useState(false);
  const [error, setError] = useState<string|undefined>(undefined);

  // 1) Initialize WebSocket once
  useEffect(() => {
    if (Platform.OS === 'web') return;
    const ws = new WebSocket(wsUrl);
    ws.binaryType = 'arraybuffer';
    ws.onopen = () => console.log('✅ WebSocket open');
    ws.onerror = (e) => {
      console.warn('🔴 WebSocket error', e);
      setError('WebSocket error');
    };
    ws.onclose = () => console.log('⚪ WebSocket closed');
    wsRef.current = ws;
    return () => ws.close();
  }, [wsUrl]);

  // 2) Configure AudioRecord
  useEffect(() => {
    if (Platform.OS === 'web') return;
    const options: AudioRecordOptions = {
      sampleRate: 16000,   // match backend expectations
      channels: 1,
      bitsPerSample: 16,
      wavFile: 'recording.wav',
    };
    AudioRecord.init(options);
  }, []);

  const start = useCallback(async () => {
    if (Platform.OS === 'web') {
      Alert.alert('Voice streaming only on device');
      return;
    }
    setError(undefined);
    // Ask permission (android)
    if (Platform.OS === 'android') {
      // react-native-audio-record automatically requests permission on Android
      // Optionally, you can use react-native-permissions here as well
    } else if (Platform.OS === 'ios') {
      // Uses react-native-permissions to trigger the iOS prompt
      const result = await request(PERMISSIONS.IOS.MICROPHONE);
      if (result !== RESULTS.GRANTED) {
        Alert.alert('Permission Denied', 'Cannot record without microphone permission.');
        return;
      }
    }

    setError(undefined);

    wsRef.current?.send(JSON.stringify({ type: 'start' })); // optional meta

    AudioRecord.on('data', (data: string) => {
      // data: base64‐encoded PCM chunk
      const buffer = Buffer.from(data, 'base64');
      wsRef.current?.send(buffer);
    });

    AudioRecord.start();
    setListening(true);
  }, []);

  const stop = useCallback(async () => {
    if (!listening) return;
    await AudioRecord.stop(); // stops & returns file path, but we don't use it
    setListening(false);

    wsRef.current?.send('/end'); // end‐of‐utterance sentinel
  }, [listening]);

  return { start, stop, listening, error };
}