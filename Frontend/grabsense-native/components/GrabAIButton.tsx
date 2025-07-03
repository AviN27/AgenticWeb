import { BottomTabBarButtonProps } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { Pressable } from 'react-native';

export default function GrabAIButton(props: BottomTabBarButtonProps) {
  return (
    <Pressable
      accessibilityLabel="Grab AI"
      {...props}
      style={{
        marginTop: -20,
        height: 60,
        width: 60,
        borderRadius: 30,
        backgroundColor: '#0a7ea4',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <Ionicons name="sparkles" size={28} color="white" />
    </Pressable>
  );
}
