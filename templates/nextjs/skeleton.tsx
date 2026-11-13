import { cn } from "@/lib/utils";

/** Content placeholder. Match the final layout's size so nothing shifts when data arrives. */
export function Skeleton({ className }: { className?: string }) {
  return <div aria-hidden className={cn("animate-pulse rounded-md bg-muted motion-reduce:animate-none", className)} />;
}
