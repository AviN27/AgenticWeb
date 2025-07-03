import { Ionicons } from '@expo/vector-icons';
import { FlatList, Pressable, StyleSheet, View, Alert } from 'react-native';

import HomeTile from '@/components/HomeTile';
import RecCard, { Rec } from '@/components/RecCard';
import { ThemedText } from '@/components/ThemedText';

import sampleRecs from '@/data/sample-recs.json';

const TILES = [
  { label: 'Transport', icon: 'car-outline' as const },
  { label: 'Mart', icon: 'basket-outline' as const },
  { label: 'Mart (food)', icon: 'fast-food-outline' as const },
  { label: 'Express', icon: 'rocket-outline' as const },
  { label: 'Dine Out', icon: 'restaurant-outline' as const },
  { label: 'Chope', icon: 'calendar-outline' as const },
  { label: 'Shopping', icon: 'cart-outline' as const },
  { label: 'All', icon: 'apps-outline' as const },
];

export default function HomeScreen() {
  const handleAddCard = () => Alert.alert('Add Card');

  return (
    <View style={styles.container}>
      <View style={styles.grid}>
        {TILES.map((tile) => (
          <HomeTile key={tile.label} label={tile.label} icon={tile.icon} />
        ))}
      </View>

      <View style={styles.cardsRow}>
        {[1, 2].map((id) => (
          <Pressable key={id} style={styles.card} onPress={handleAddCard}>
            <Ionicons name="add" size={24} color="#0a7ea4" />
            <ThemedText>Add a Card</ThemedText>
          </Pressable>
        ))}
      </View>

      <ThemedText type="subtitle" style={styles.recTitle}>
        Recommended
      </ThemedText>
      <FlatList
        horizontal
        data={sampleRecs as Rec[]}
        keyExtractor={(item) => String(item.id)}
        renderItem={({ item }) => <RecCard {...item} />}
        showsHorizontalScrollIndicator={false}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  cardsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginVertical: 16,
  },
  card: {
    alignItems: 'center',
    justifyContent: 'center',
    width: '48%',
    height: 80,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
  },
  recTitle: {
    marginBottom: 8,
  },