// Loading Skeleton Component
import React from 'react';
import { View, StyleSheet, Animated } from 'react-native';
import { theme } from '../theme';

interface SkeletonProps {
  width?: number | string;
  height?: number;
  borderRadius?: number;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  width = '100%',
  height = 20,
  borderRadius = theme.borderRadius.md,
}) => {
  const pulseAnim = React.useRef(new Animated.Value(0)).current;

  React.useEffect(() => {
    const animation = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 1000,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 0,
          duration: 1000,
          useNativeDriver: true,
        }),
      ])
    );
    animation.start();

    return () => animation.stop();
  }, [pulseAnim]);

  const opacity = pulseAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0.3, 0.7],
  });

  return (
    <Animated.View
      style={[
        styles.skeleton,
        { width, height, borderRadius, opacity },
      ]}
    />
  );
};

// Deal Card Skeleton
export const DealCardSkeleton: React.FC = () => {
  return (
    <View style={cardStyles.container}>
      <View style={cardStyles.content}>
        <Skeleton width={80} height={80} borderRadius={theme.borderRadius.md} />
        <View style={cardStyles.info}>
          <Skeleton width={60} height={12} />
          <Skeleton width="80%" height={20} style={{ marginTop: 4 }} />
          <View style={cardStyles.priceRow}>
            <Skeleton width={80} height={24} />
            <Skeleton width={50} height={16} style={{ marginLeft: 8 }} />
          </View>
          <View style={cardStyles.metaRow}>
            <Skeleton width={60} height={20} borderRadius={4} />
            <Skeleton width={100} height={14} style={{ marginLeft: 8 }} />
          </View>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  skeleton: {
    backgroundColor: theme.colors.surfaceVariant,
  },
});

const cardStyles = StyleSheet.create({
  container: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.lg,
    marginHorizontal: theme.spacing.md,
    marginVertical: theme.spacing.sm,
    padding: theme.spacing.md,
    ...theme.shadows.md,
  },
  content: {
    flexDirection: 'row',
  },
  info: {
    flex: 1,
    marginLeft: theme.spacing.md,
    justifyContent: 'center',
  },
  priceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: theme.spacing.sm,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: theme.spacing.sm,
  },
});

export default Skeleton;
