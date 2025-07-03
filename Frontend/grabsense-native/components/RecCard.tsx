import { Image } from 'expo-image';
import { View, StyleSheet } from 'react-native';
import { ThemedText } from './ThemedText';

export type Rec = {
  id: number;
  name: string;
  distance: string;
  rating: number;
  image: string;
};

export default function RecCard({ name, distance, rating, image }: Rec) {
  return (
    <View style={styles.card}>
      <Image source={{ uri: image }} style={styles.image} contentFit="cover" />
      <ThemedText style={styles.name}>{name}</ThemedText>
      <ThemedText>{distance} • {rating.toFixed(1)}</ThemedText>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    width: 160,
    marginRight: 12,
  },
  image: {
    width: '100%',
    height: 100,
    borderRadius: 8,
    marginBottom: 4,
  },
  name: {
    fontWeight: '600',
  },
});
