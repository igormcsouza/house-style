import { ActivityIndicator, Pressable, Text } from "react-native";

/** Keeps its label, shows a spinner in place while pending. Min 44px touch target. */
export function ActionButton({ title, onPress, pending, disabled }: { title: string; onPress: () => void; pending?: boolean; disabled?: boolean }) {
  const off = disabled || pending;
  return (
    <Pressable
      onPress={onPress}
      disabled={off}
      accessibilityRole="button"
      accessibilityLabel={title}
      accessibilityState={{ disabled: off, busy: pending }}
      className={`min-h-11 flex-row items-center justify-center gap-2 rounded-lg bg-primary px-4 active:scale-[0.98] ${off ? "opacity-50" : ""}`}
    >
      {pending && <ActivityIndicator size="small" />}
      <Text className="font-medium text-primary-foreground">{title}</Text>
    </Pressable>
  );
}
