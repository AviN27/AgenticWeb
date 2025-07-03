import React from 'react';
import {
  SafeAreaView,
  ScrollView,
  View,
  TextInput,
  StyleSheet,
  Pressable,
  FlatList,
  Text,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import HomeTile from '@/components/HomeTile';
import RecCard, { Rec } from '@/components/RecCard';
import sampleRecs from '@/data/sample-recs.json';

const TILES: { label: string; icon: keyof typeof Ionicons.glyphMap }[] = [
  { label: 'Transport', icon: 'car-outline' },
  { label: 'Mart', icon: 'basket-outline' },
  { label: 'Delivery', icon: 'fast-food-outline' },
  { label: 'Express', icon: 'rocket-outline' },
  { label: 'Dine Out', icon: 'restaurant-outline' },
  { label: 'Chope', icon: 'calendar-outline' },
  { label: 'Shopping', icon: 'cart-outline' },
  { label: 'All', icon: 'apps-outline' },
];

export default function HomeScreen() {
  const handleAddCard = () => {
    console.log('Add Card tapped');
  };

  return (
    <SafeAreaView style={styles.safe}>
      {/* HEADER */}
      <View style={styles.header}>
        <Ionicons name="scan-outline" size={24} color="#fff" />
        <View style={styles.searchWrapper}>
          <Ionicons name="search-outline" size={20} color="#888" />
          <TextInput
            placeholder="Search the Grab app"
            placeholderTextColor="#888"
            style={styles.searchInput}
          />
        </View>
        <Ionicons name="person-circle-outline" size={28} color="#fff" />
      </View>

      <ScrollView contentContainerStyle={styles.container}>
        {/* 4 × 2 GRID */}
        <View style={styles.grid}>
          {TILES.map((tile) => (
            <HomeTile
              key={tile.label}
              icon={tile.icon}
              label={tile.label}
            />
          ))}
        </View>

        {/* PAYMENT CARDS */}
        <View style={styles.cardsRow}>
          {[1, 2].map((id) => (
            <Pressable
              key={id}
              onPress={handleAddCard}
              style={styles.addCard}
            >
              <Ionicons name="add" size={20} color="#0A7EA4" />
              <Text style={styles.addCardText}>Add a Card</Text>
            </Pressable>
          ))}
        </View>

        {/* SECTION HEADER */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Restaurants you may like</Text>
          <Pressable>
            <Ionicons name="chevron-forward" size={24} color="#0A7EA4" />
          </Pressable>
        </View>

        {/* RECS CAROUSEL */}
        <FlatList
          horizontal
          data={sampleRecs as Rec[]}
          keyExtractor={(item) => String(item.id)}
          renderItem={({ item }) => (
            <View style={styles.recWrapper}>
              <RecCard {...item} />
            </View>
          )}
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={{ paddingHorizontal: 16 }}
        />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#fff' },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#6DD5FA',
    ...Platform.select({
      android: { elevation: 4 },
      ios: { shadowColor: '#000', shadowOpacity: 0.1, shadowOffset: { width: 0, height: 2 }, shadowRadius: 4 },
    }),
    justifyContent: 'space-between',
  },
  searchWrapper: {
    flex: 1,
    flexDirection: 'row',
    backgroundColor: '#fff',
    marginHorizontal: 12,
    paddingHorizontal: 8,
    alignItems: 'center',
    borderRadius: 24,
    height: 40,
  },
  searchInput: {
    flex: 1,
    marginLeft: 6,
    fontSize: 16,
    color: '#333',
  },
  container: {
    padding: 16,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -8, // to offset the 8px padding on each HomeTile wrapper
  },
  cardsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginVertical: 24,
  },
  addCard: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F6F9FC',
    borderRadius: 12,
    height: 80,
    marginHorizontal: 4,
    borderWidth: 1,
    borderColor: '#E1E8F0',
  },
  addCardText: {
    marginLeft: 8,
    fontSize: 16,
    fontWeight: '600',
    color: '#0A7EA4',
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111',
  },
  recWrapper: {
    marginRight: 16,
    width: 200,
  },
});
