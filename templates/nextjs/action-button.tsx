import * as React from "react";
import { Button } from "@/components/ui/button"; // shadcn
import { Spinner } from "./spinner";

/** Button that shows progress in place: keeps its label and width, disables itself while pending. */
export function ActionButton({ pending, children, disabled, ...props }: React.ComponentProps<typeof Button> & { pending?: boolean }) {
  return (
    <Button {...props} disabled={disabled || pending} aria-busy={pending}>
      {pending && <Spinner />}
      {children}
    </Button>
  );
}
