# Olfex Mobile App

React Native mobile app for niche perfume deal hunting. Built with Expo, React Navigation, and Redux Toolkit.

## Features

- 🔥 **Deal Feed**: Real-time deals from top retailers
- 🔍 **Browse**: Search and explore niche perfumes
- 🚨 **Price Alerts**: Get notified when prices drop
- 👤 **Profile**: Manage preferences and view stats

## Tech Stack

- **Framework**: Expo SDK 52 + React Native
- **Navigation**: React Navigation v6
- **State**: Redux Toolkit + RTK Query
- **UI**: React Native Paper
- **Charts**: React Native Chart Kit
- **Notifications**: Expo Notifications

## Project Structure

```
src/
├── api/              # API client and RTK Query slices
├── components/       # Reusable UI components
├── navigation/       # Navigation configuration
├── screens/          # Screen components
├── store/            # Redux store and slices
├── theme/            # Theme configuration
├── types/            # TypeScript types
└── utils/            # Utility functions
```

## Getting Started

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Configure API endpoint**:
   Set `EXPO_PUBLIC_API_URL` in your environment or update `src/api/client.ts`

3. **Start the app**:
   ```bash
   npx expo start
   ```

4. **Run on device/simulator**:
   - Press `i` for iOS simulator
   - Press `a` for Android emulator
   - Scan QR code with Expo Go app

## Environment Variables

```bash
EXPO_PUBLIC_API_URL=http://localhost:8001/api
```

## Scripts

- `npm start` - Start Expo development server
- `npm run android` - Run on Android
- `npm run ios` - Run on iOS
- `npm run web` - Run on web
- `npm run type-check` - Run TypeScript checks

## API Integration

The app connects to a FastAPI backend at `localhost:8001` with endpoints:

- `GET /api/perfumes` - List all perfumes
- `GET /api/deals` - List active deals
- `GET /api/alerts` - User's price alerts

## License

MIT
