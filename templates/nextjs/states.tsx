import type { ReactNode } from "react";
import { AlertCircle, Inbox, type LucideIcon } from "lucide-react";
import { Button } from "@/components/ui/button"; // shadcn

export function EmptyState({ icon: Icon = Inbox, title, hint, action }: { icon?: LucideIcon; title: string; hint?: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-3 py-16 text-center">
      <Icon aria-hidden className="size-8 text-muted-foreground" />
      <h2 className="text-lg font-semibold">{title}</h2>
      {hint && <p className="max-w-sm text-sm text-muted-foreground">{hint}</p>}
      {action}
    </div>
  );
}

/** Keep any previously loaded data visible next to this; never replace it with a blank error page. */
export function ErrorState({ title = "Something went wrong", detail, onRetry }: { title?: string; detail?: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex flex-col items-center gap-3 py-16 text-center">
      <AlertCircle aria-hidden className="size-8 text-destructive" />
      <h2 className="text-lg font-semibold">{title}</h2>
      {detail && <p className="max-w-sm text-sm text-muted-foreground">{detail}</p>}
      {onRetry && <Button variant="outline" onClick={onRetry}>Try again</Button>}
    </div>
  );
}
