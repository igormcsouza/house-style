# Loading, empty, error (Doherty threshold: respond within 400ms)

| Situation | Pattern |
|---|---|
| Page/section content loading | Skeleton matching the final layout (same heights), `animate-pulse motion-reduce:animate-none`, Next `loading.tsx` per route |
| User action (submit, save) | Same button: keep label, show Lucide `Loader2` (`animate-spin motion-reduce:animate-none`) before it, `aria-busy`, `disabled` |
| Background refresh | Keep stale data visible + subtle inline spinner; never blank the view |
| Long job (>10s) | Progress or step text + cancel; poll with backoff; announce completion via `aria-live` |
| Instant (<100ms) | Show nothing. Delay spinners ~150ms to avoid flicker |
| Navigation | Route-level skeleton, keep shell (header/nav) mounted |
Banned: blocking full-screen spinner, indeterminate spinner for content that has a known shape, text "Loading..." alone with no skeleton.

Every list/view defines all four states:
1. loading (skeleton) 2. empty (project icon or Lucide glyph + one sentence + primary action) 3. error (`AlertCircle` icon + what happened + Retry; keep prior data) 4. success.
Mutations: optimistic update, rollback + error toast on failure, undo toast for deletes.
Native: `ActivityIndicator` inside `ActionButton`; skeletons with reanimated opacity pulse; respect reduce-motion (`useReducedMotion`).
