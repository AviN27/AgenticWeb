// src/hooks/useSSE.ts
import { useState, useEffect, useRef, useCallback } from 'react';
import { Platform } from 'react-native';

interface SSEOptions {
  url: string;
  initPayload?: Record<string, any>;
  onOpen?: () => void;
  onError?: (err: any) => void;
}

type Connection = {
  close: () => void;
};

export default function useSSE() {
  const [data, setData] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<any>(null);
  const connRef = useRef<Connection | null>(null);

  const connect = useCallback(
    ({ url, initPayload, onOpen, onError }: SSEOptions) => {
      // tear down old
      connRef.current?.close();
      setIsConnected(false);
      setError(null);
      setData(null);

      // build query string
      const qs = initPayload
        ? '?' +
          Object.entries(initPayload)
            .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
            .join('&')
        : '';

      // WEB: Use real SSE
      if (Platform.OS === 'web' && typeof EventSource !== 'undefined') {
        const es = new EventSource(url + qs, { withCredentials: false });
        connRef.current = es;
        es.onopen = () => {
          setIsConnected(true);
          onOpen?.();
        };
        es.onmessage = (evt) => setData(evt.data);
        es.onerror = (err) => {
          setError(err);
          setIsConnected(false);
          onError?.(err);
          es.close();
        };
        return;
      }

      // NATIVE: fallback to WebSocket
      const wsUrl = url.replace(/^http/, (url.startsWith('https') ? 'wss' : 'ws')) + qs;
      const ws = new WebSocket(wsUrl);
      connRef.current = ws as unknown as Connection;

      ws.onopen = () => {
        setIsConnected(true);
        onOpen?.();
      };
      ws.onmessage = (evt) => setData(evt.data);
      ws.onerror = (e) => {
        setError(e);
        setIsConnected(false);
        onError?.(e);
        ws.close();
      };
      ws.onclose = () => {
        setIsConnected(false);
      };
    },
    []
  );

  const disconnect = useCallback(() => {
    connRef.current?.close();
    connRef.current = null;
    setIsConnected(false);
  }, []);

  useEffect(() => () => connRef.current?.close(), []);

  return { data, isConnected, error, connect, disconnect };
}