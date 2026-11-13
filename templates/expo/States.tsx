import { Text, View } from "react-native";
import { AlertCircle, Inbox, type LucideIcon } from "lucide-react-native";
import { ActionButton } from "./ActionButton";

export function EmptyState({ icon: Icon = Inbox, title, hint }: { icon?: LucideIcon; title: string; hint?: string }) {
  return (
    <View className="items-center gap-3 py-16">
      <Icon size={32} className="text-muted-foreground" />
      <Text className="text-lg font-semibold text-foreground">{title}</Text>
      {hint && <Text className="text-center text-sm text-muted-foreground">{hint}</Text>}
    </View>
  );
}

export function ErrorState({ title = "Something went wrong", onRetry }: { title?: string; onRetry?: () => void }) {
  return (
    <View accessibilityRole="alert" className="items-center gap-3 py-16">
      <AlertCircle size={32} className="text-destructive" />
      <Text className="text-lg font-semibold text-foreground">{title}</Text>
      {onRetry && <ActionButton title="Try again" onPress={onRetry} />}
    </View>
  );
}
