// src/screens/GrabAI.tsx
import React, { useEffect, useRef } from 'react';
import {
  SafeAreaView,
  View,
  Text,
  Pressable,
  FlatList,
  StyleSheet,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import useVoice from '@/hooks/useVoice';

type Message = { id: string; text: string; from: 'user' | 'assistant' };

export default function GrabAI() {
  const { listening, transcript, error, start, stop } = useVoice();
  const [messages, setMessages] = React.useState<Message[]>([]);
  const flatRef = useRef<FlatList>(null);

  // Whenever transcript updates, push it as a user message
  useEffect(() => {
    if (!transcript) return;
    setMessages((m) => [
      ...m,
      { id: Date.now().toString(), text: transcript, from: 'user' },
    ]);
  }, [transcript]);

  // scroll on new messages
  useEffect(() => {
    flatRef.current?.scrollToEnd({ animated: true });
  }, [messages]);

  const toggleRecord = () => {
    listening ? stop() : start();
  };

  return (
    <SafeAreaView style={styles.safe}>
      <FlatList
        ref={flatRef}
        data={messages}
        keyExtractor={(m) => m.id}
        contentContainerStyle={styles.chat}
        renderItem={({ item }) => (
          <View
            style={[
              styles.bubble,
              item.from === 'user' ? styles.userBubble : styles.aiBubble,
            ]}
          >
            <Text style={ item.from === 'user' ? styles.userText : styles.aiText }>
              {item.text}
            </Text>
          </View>
        )}
      />

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <View style={styles.inputRow}>
        <Pressable onPress={toggleRecord} style={styles.micButton}>
          <Ionicons
            name={listening ? 'mic' : 'mic-outline'}
            size={28}
            color={listening ? '#E91E63' : '#555'}
          />
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F6F6F6' },
  chat: { padding: 16, paddingBottom: 100 },
  bubble: { marginVertical: 4, padding: 12, borderRadius: 16 },
  userBubble: { backgroundColor: '#0A7EA4', alignSelf: 'flex-end' },
  aiBubble: { backgroundColor: '#EEE', alignSelf: 'flex-start' },
  userText: { color: '#fff' },
  aiText: { color: '#111' },
  error: { color: 'red', textAlign: 'center', marginVertical: 4 },
  inputRow: {
    position: 'absolute',
    bottom: 32,
    left: 0,
    right: 0,
    alignItems: 'center',
  },
  micButton: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#fff',
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 4,
  },
});
