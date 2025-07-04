import { Stack } from 'expo-router';

export default function HomeStack() {
  return (
    <Stack>
      <Stack.Screen name="index" options={{ headerShown: false }} />
      <Stack.Screen name="assistant-sheet" options={{ title: 'Assistant' }} />
      <Stack.Screen name="status-tracker" options={{ title: 'Status' }} />
    </Stack>
  );
}
