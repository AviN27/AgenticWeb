import React from 'react';
import { Pressable, StyleSheet, Platform, ViewStyle } from 'react-native';
import { useRouter } from 'expo-router';

interface Props {
  accessibilityState?: { selected?: boolean };
  style?: ViewStyle[] | ViewStyle;
}

export default function GrabAIButton({ accessibilityState, style, ...rest }: Props) {
  const router = useRouter();
  const focused = accessibilityState?.selected;

  return (
    <Pressable
      {...rest}
      onPress={() => router.push('/grab-ai')}
      style={[
        styles.button,
        focused ? styles.focused : null,
        style as any,
      ]}
    />
  );
}

const styles = StyleSheet.create({
  button: {
    position: 'absolute',
    bottom: Platform.OS === 'ios' ? 34 : 16,
    alignSelf: 'center',
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: '#00C853',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOpacity: 0.2,
    shadowOffset: { width: 0, height: 4 },
    shadowRadius: 6,
    elevation: 5,
  },
  focused: {
    backgroundColor: '#018E42', // darker when active
  },
});