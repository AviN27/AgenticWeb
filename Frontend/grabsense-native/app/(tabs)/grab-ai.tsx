import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  Pressable,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  ActivityIndicator,
  SafeAreaView
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import useSSE from '@/hooks/useSSE';        
import useSpeech from '@/hooks/useSpeech';

type Message = {
  id: string;
  text: string;
  from: 'user' | 'assistant';
};

export default function GrabAI() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const flatListRef = useRef<FlatList>(null);

  // speech-to-text hook
  const { transcript, listening, record, stop } = useSpeech();

  // SSE streaming hook: sends a prompt, receives chunks
  const { connect, isConnected, data: chunk, error } = useSSE();

  // when a new chunk arrives, append to last assistant message
  useEffect(() => {
    if (!chunk) return;
    setMessages((prev) => {
      const last = prev[prev.length - 1];
      if (last && last.from === 'assistant') {
        // append to existing
        return [
          ...prev.slice(0, -1),
          { ...last, text: last.text + chunk },
        ];
      }
      return prev;
    });
  }, [chunk]);

  // helper to scroll to bottom on new message
  useEffect(() => {
    flatListRef.current?.scrollToEnd({ animated: true });
  }, [messages]);

  const sendMessage = () => {
    if (!input.trim()) return;
    const userMsg: Message = {
      id: Date.now().toString(),
      text: input.trim(),
      from: 'user',
    };
    setMessages((prev) => [...prev, userMsg]);

    // kick off assistant response
    const assistantMsg: Message = {
      id: `a-${Date.now()}`,
      text: '',
      from: 'assistant',
    };
    setMessages((prev) => [...prev, assistantMsg]);

    connect({
      url: `${process.env.BACKEND_BASE_URL}/v1/stream/updates`,
      initPayload: { prompt: input.trim() },
    });

    setInput('');
  };

  const toggleListen = () => {
    if (listening) {
      stop();
      setInput(transcript);
    } else {
      record();
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.select({ ios: 'padding', android: undefined })}
        keyboardVerticalOffset={90}
      >
        <FlatList
          ref={flatListRef}
          data={messages}
          keyExtractor={(msg) => msg.id}
          contentContainerStyle={[styles.chatContainer, styles.chatContainerInset]}
          renderItem={({ item }) => (
            <View
              style={[
                styles.bubble,
                item.from === 'user' ? styles.userBubble : styles.aiBubble,
              ]}
            >
              <Text
                style={[
                  styles.bubbleText,
                  item.from === 'user' ? styles.userText : styles.aiText,
                ]}
              >
                {item.text}
              </Text>
            </View>
          )}
        />

        <View style={[styles.inputRow, styles.inputRowInset]}>
          <Pressable onPress={toggleListen} style={styles.iconButton}>
            <Ionicons
              name={listening ? 'mic' : 'mic-outline'}
              size={24}
              color={listening ? '#0A7EA4' : '#888'}
            />
          </Pressable>

          <TextInput
            style={styles.textInput}
            placeholder="Type or tap mic to speak..."
            value={input}
            onChangeText={setInput}
            onSubmitEditing={sendMessage}
            returnKeyType="send"
          />

          {isConnected ? (
            <ActivityIndicator style={styles.loader} />
          ) : (
            <Pressable onPress={sendMessage} style={styles.iconButton}>
              <Ionicons name="send" size={24} color="#0A7EA4" />
            </Pressable>
          )}
        </View>
        {error ? <Text style={styles.error}>Connection error. Try again.</Text> : null}
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F6F6F6' },
  flex: { flex: 1 },
  chatContainer: {
    padding: 16,
    paddingBottom: 8,
  },
  chatContainerInset: {
    paddingBottom: Platform.OS === 'ios' ? 120 : 100,
  },
  bubble: {
    maxWidth: '80%',
    marginVertical: 4,
    padding: 12,
    borderRadius: 16,
  },
  userBubble: {
    backgroundColor: '#0A7EA4',
    alignSelf: 'flex-end',
    borderBottomRightRadius: 4,
  },
  aiBubble: {
    backgroundColor: '#FFFFFF',
    alignSelf: 'flex-start',
    borderBottomLeftRadius: 4,
  },
  bubbleText: {
    fontSize: 16,
    lineHeight: 22,
  },
  userText: {
    color: '#FFFFFF',
  },
  aiText: {
    color: '#111111',
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderTopWidth: 1,
    borderColor: '#E1E8F0',
    backgroundColor: '#FFFFFF',
  },
  inputRowInset: {
    paddingBottom: Platform.OS === 'ios' ? 50 : 32,
  },
  iconButton: {
    padding: 8,
  },
  textInput: {
    flex: 1,
    marginHorizontal: 8,
    backgroundColor: '#F0F9FF',
    borderRadius: 20,
    paddingHorizontal: 12,
    height: 40,
    fontSize: 16,
  },
  loader: {
    padding: 8,
  },
  error: {
    color: '#D32F2F',
    textAlign: 'center',
    padding: 4,
  },
});