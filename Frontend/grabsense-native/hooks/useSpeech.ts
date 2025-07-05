// src/hooks/useSpeech.ts
import { useState, useEffect, useCallback } from 'react';
import { AudioModule, useAudioRecorder, RecordingPresets } from 'expo-audio';
import * as FileSystem from 'expo-file-system';
import { Alert } from 'react-native';
import useMicSocket from './useMicSocket';

export default function useSpeech() {
  const [transcript, setTranscript] = useState('');
  const [listening, setListening] = useState(false);
  const audioRecorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);
  const { connect, send, end, onMessage, onError } = useMicSocket();

  // ask for permission once
  useEffect(() => {
    (async () => {
      const { granted } = await AudioModule.requestRecordingPermissionsAsync();
      if (!granted) {
        Alert.alert('Permission to access microphone was denied');
      }
    })();
  }, []);

  // handle messages from server (ASR text)
  useEffect(() => {
    onMessage((msg) => {
      setTranscript(msg);
    });
    onError((err) => {
      console.error('Mic socket error', err);
    });
  }, [onMessage, onError]);

  const record = useCallback(async () => {
    // open socket first
    connect(process.env.BACKEND_BASE_URL!);
    await audioRecorder.prepareToRecordAsync();
    audioRecorder.record();
    setListening(true);
  }, [audioRecorder, connect]);

  const stop = useCallback(async () => {
    try {
      await audioRecorder.stop();
      setListening(false);

      const uri = audioRecorder.uri;
      if (!uri) return;

      // read file as base64
      const b64 = await FileSystem.readAsStringAsync(uri, {
        encoding: FileSystem.EncodingType.Base64,
      });

      // send binary (hex or base64) over WS
      send(b64);

      // tell backend end of utterance
      end();

      // transcript will be set in onMessage when server replies
    } catch (err) {
      console.error('stop recording error', err);
    }
  }, [audioRecorder, send, end]);

  return { transcript, listening, record, stop };
}