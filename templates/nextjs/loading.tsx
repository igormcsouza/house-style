// app/loading.tsx - route-level skeleton. Mirror the real page layout; keep header/nav mounted via layout.
import { Skeleton } from "@/components/skeleton";

export default function Loading() {
  return (
    <div className="mx-auto w-full max-w-3xl space-y-4 p-6" aria-busy>
      <Skeleton className="h-8 w-1/3" />
      <Skeleton className="h-24 w-full" />
      <Skeleton className="h-24 w-full" />
    </div>
  );
}
