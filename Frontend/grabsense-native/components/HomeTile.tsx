import { Ionicons } from '@expo/vector-icons';
import { Pressable, StyleSheet } from 'react-native';

import { ThemedText } from './ThemedText';

export type HomeTileProps = {
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
  onPress?: () => void;
};

export default function HomeTile({ label, icon, onPress }: HomeTileProps) {
  return (
    <Pressable style={styles.tile} onPress={onPress} accessibilityLabel={label}>
      <Ionicons name={icon} size={32} color="#0a7ea4" />
      <ThemedText>{label}</ThemedText>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  tile: {
    alignItems: 'center',
    justifyContent: 'center',
    width: '25%',
    marginVertical: 12,
  },
});
