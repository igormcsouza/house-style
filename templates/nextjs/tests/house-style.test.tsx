import { fireEvent, render, screen } from "@testing-library/react";
import { Inbox } from "lucide-react";
import { describe, expect, it, vi } from "vitest";
import Loading from "@/app/loading";
import { ActionButton } from "@/components/action-button";
import { Skeleton } from "@/components/skeleton";
import { Spinner } from "@/components/spinner";
import { EmptyState, ErrorState } from "@/components/states";
import { ThemeToggle } from "@/components/theme-toggle";

const theme = vi.hoisted(() => ({ resolved: "light", setTheme: vi.fn() }));
vi.mock("next-themes", () => ({ useTheme: () => ({ resolvedTheme: theme.resolved, setTheme: theme.setTheme }) }));

describe("loading primitives", () => {
  it("Skeleton is hidden from assistive tech and accepts a class", () => {
    const { container } = render(<Skeleton className="h-4" />);
    expect(container.firstElementChild).toHaveAttribute("aria-hidden", "true");
    expect(container.firstElementChild).toHaveClass("h-4");
    render(<Skeleton />);
  });

  it("Spinner announces its label", () => {
    render(<Spinner label="Saving" />);
    expect(screen.getByRole("status")).toHaveTextContent("Saving");
    render(<Spinner />);
    expect(screen.getAllByRole("status")).toHaveLength(2);
  });

  it("route loading page is busy", () => {
    const { container } = render(<Loading />);
    expect(container.firstElementChild).toHaveAttribute("aria-busy", "true");
  });
});

describe("ActionButton", () => {
  it("disables itself and shows a spinner while pending, keeping its label", () => {
    render(<ActionButton pending>Save</ActionButton>);
    const button = screen.getByRole("button", { name: /save/i });
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("aria-busy", "true");
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("is a normal button when idle", () => {
    const onClick = vi.fn();
    render(<ActionButton onClick={onClick}>Save</ActionButton>);
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(onClick).toHaveBeenCalledOnce();
    expect(screen.queryByRole("status")).toBeNull();
  });
});

describe("states", () => {
  it("EmptyState shows title, hint and action", () => {
    render(<EmptyState icon={Inbox} title="Nothing yet" hint="Create one" action={<button>Add</button>} />);
    expect(screen.getByRole("heading", { name: "Nothing yet" })).toBeInTheDocument();
    expect(screen.getByText("Create one")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add" })).toBeInTheDocument();
  });

  it("EmptyState works with defaults", () => {
    render(<EmptyState title="Empty" />);
    expect(screen.getByRole("heading", { name: "Empty" })).toBeInTheDocument();
  });

  it("ErrorState is an alert with a retry", () => {
    const retry = vi.fn();
    render(<ErrorState detail="Boom" onRetry={retry} />);
    expect(screen.getByRole("alert")).toHaveTextContent("Something went wrong");
    expect(screen.getByText("Boom")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /try again/i }));
    expect(retry).toHaveBeenCalledOnce();
  });

  it("ErrorState works with defaults", () => {
    render(<ErrorState title="Custom" />);
    expect(screen.getByRole("alert")).toHaveTextContent("Custom");
    expect(screen.queryByRole("button")).toBeNull();
  });
});

describe("ThemeToggle", () => {
  it("switches light -> dark with an accessible name", () => {
    theme.resolved = "light";
    render(<ThemeToggle />);
    fireEvent.click(screen.getByRole("button", { name: "Switch to dark theme" }));
    expect(theme.setTheme).toHaveBeenCalledWith("dark");
  });

  it("switches dark -> light", () => {
    theme.resolved = "dark";
    render(<ThemeToggle />);
    fireEvent.click(screen.getByRole("button", { name: "Switch to light theme" }));
    expect(theme.setTheme).toHaveBeenCalledWith("light");
  });
});
