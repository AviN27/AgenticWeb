const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);
config.resolver.extraNodeModules = {
  // whenever code does `import 'eventsource'` or uses global EventSource,
  // redirect to the native shim:
  eventsource: require.resolve('react-native-event-source'),
};

module.exports = config;