import { useState, useEffect, useCallback } from 'react';
import Voice from '@react-native-voice/voice';
import { NativeEventEmitter, NativeModules, Platform, Alert } from 'react-native';
import { check, request, PERMISSIONS, RESULTS } from 'react-native-permissions'; // <-- Add this

const { Voice: VoiceModule } = NativeModules;
const voiceEmitter = new NativeEventEmitter(VoiceModule);

export default function useVoice() {
  const [listening, setListening] = useState(false);
  const [transcript, setTranscript] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Request microphone permission on mount
    async function requestMicrophone() {
      let permission;
      if (Platform.OS === 'ios') {
        permission = PERMISSIONS.IOS.MICROPHONE;
      } else if (Platform.OS === 'android') {
        permission = PERMISSIONS.ANDROID.RECORD_AUDIO;
      }
      if (permission) {
        const status = await check(permission);
        if (status !== RESULTS.GRANTED) {
          const result = await request(permission);
          if (result !== RESULTS.GRANTED) {
            Alert.alert('Permission required', 'Microphone access is needed for voice recognition.');
          }
        }
      }
    }
    requestMicrophone();

    // Bind events via the emitter
    const subs = [
      voiceEmitter.addListener('onSpeechStart', () => setListening(true)),
      voiceEmitter.addListener('onSpeechResults', (e: any) => {
        if (e.value?.length) setTranscript(e.value[0]);
      }),
      voiceEmitter.addListener('onSpeechEnd', () => setListening(false)),
      voiceEmitter.addListener('onSpeechError', (e: any) => {
        setError(e.error.message);
        setListening(false);
      }),
    ];

    return () => {
      // Clean up
      subs.forEach((sub) => sub.remove());
      Voice.destroy().then(Voice.removeAllListeners);
    };
  }, []);

  const start = useCallback(async () => {
    setError(null);
    setTranscript('');
    try {
      await Voice.start('en-US');
    } catch (e: any) {
      setError(e.message);
    }
  }, []);

  const stop = useCallback(async () => {
    try {
      await Voice.stop();
    } catch (e: any) {
      setError(e.message);
    }
  }, []);

  return { listening, transcript, error, start, stop };
}