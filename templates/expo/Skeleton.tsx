import { useEffect } from "react";
import { View } from "react-native";
import Animated, { useAnimatedStyle, useReducedMotion, useSharedValue, withRepeat, withTiming } from "react-native-reanimated";

export function Skeleton({ className = "h-6 w-full" }: { className?: string }) {
  const o = useSharedValue(1);
  const reduce = useReducedMotion();
  useEffect(() => {
    if (!reduce) o.value = withRepeat(withTiming(0.5, { duration: 900 }), -1, true);
  }, [reduce, o]);
  const style = useAnimatedStyle(() => ({ opacity: o.value }));
  return (
    <View importantForAccessibility="no-hide-descendants" accessibilityElementsHidden>
      <Animated.View style={style} className={`rounded-md bg-muted ${className}`} />
    </View>
  );
}
