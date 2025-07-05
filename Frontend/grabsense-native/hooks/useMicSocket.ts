// src/hooks/useMicSocket.ts
import { useRef, useCallback } from 'react';
import { Platform } from 'react-native';

export default function useMicSocket() {
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback((baseUrl: string) => {
    // build ws:// or wss:// from HTTP
    const url = baseUrl.replace(/^http/, baseUrl.startsWith('https') ? 'wss' : 'ws') + '/ws/mic';
    const ws = new WebSocket(url);
    wsRef.current = ws;
  }, []);

  const send = useCallback((data: string | ArrayBuffer) => {
    wsRef.current?.send(data);
  }, []);

  const end = useCallback(() => {
    wsRef.current?.send('/end');
    wsRef.current?.close();
  }, []);

  const onMessage = useCallback((handler: (msg: string) => void) => {
    if (wsRef.current) {
      wsRef.current.onmessage = (evt) => handler(evt.data);
    }
  }, []);

  const onError = useCallback((handler: (err: any) => void) => {
    if (wsRef.current) {
      wsRef.current.onerror = (e) => handler(e);
    }
  }, []);

  return { connect, send, end, onMessage, onError };
}