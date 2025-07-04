//shim
declare module 'react-native-event-source' {
  // default-export a constructor matching the browser API
  export default class EventSource {
    constructor(url: string, options?: { withCredentials?: boolean });
    onopen: (() => void) | null;
    onmessage: ((evt: { data: string }) => void) | null;
    onerror: ((err: any) => void) | null;
    close(): void;
  }
}

// Expose it as a global, too
declare global {
  var EventSource: typeof import('react-native-event-source').default;
}
