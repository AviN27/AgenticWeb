import { useEffect, useRef, useState, useCallback } from "react";

// Usage: const { messages, sendMessage, connectionStatus } = useWebSocket(WS_URL);
export default function useWebSocket(url) {
  const [messages, setMessages] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState("connecting");
  const ws = useRef(null);

  useEffect(() => {
    ws.current = new window.WebSocket(url);
    ws.current.onopen = () => setConnectionStatus("open");
    ws.current.onclose = () => setConnectionStatus("closed");
    ws.current.onerror = () => setConnectionStatus("error");
    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setMessages((prev) => [...prev, data]);
      } catch (e) {
        // fallback for non-JSON messages
        setMessages((prev) => [...prev, { type: "raw", data: event.data }]);
      }
    };
    return () => {
      ws.current && ws.current.close();
    };
  }, [url]);

  const sendMessage = useCallback((msg) => {
    if (ws.current && ws.current.readyState === 1) {
      ws.current.send(typeof msg === "string" ? msg : JSON.stringify(msg));
    }
  }, []);

  return { messages, sendMessage, connectionStatus };
} 