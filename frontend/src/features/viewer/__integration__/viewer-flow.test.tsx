import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import App from "@/App";
import { renderWithProviders } from "@/test/utils";


describe("viewer portal flow", () => {
  it("renders viewer login and enters the viewer dashboard", async () => {
    const user = userEvent.setup();
    window.history.replaceState({}, "", "/viewer");

    renderWithProviders(<App />);

    expect(await screen.findByText("Viewer Portal")).toBeInTheDocument();

    await user.type(screen.getByLabelText("API Key"), "sk-clb-test-viewer");
    await user.click(screen.getByRole("button", { name: "Sign In" }));

    expect(await screen.findByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Quota" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Settings" })).toBeInTheDocument();
    expect(screen.queryByText("Accounts")).not.toBeInTheDocument();
    expect(screen.getByText("Requests")).toBeInTheDocument();
    expect(screen.getByText("Tokens")).toBeInTheDocument();
    expect(screen.getByText("Cached")).toBeInTheDocument();
    expect(screen.getByText("Cost")).toBeInTheDocument();
  });

  it("supports viewer key regeneration", async () => {
    const user = userEvent.setup();
    window.history.replaceState({}, "", "/viewer");

    renderWithProviders(<App />);

    await user.type(await screen.findByLabelText("API Key"), "sk-clb-test-viewer");
    await user.click(screen.getByRole("button", { name: "Sign In" }));
    await screen.findByRole("heading", { name: "Dashboard" });

    await user.click(screen.getByRole("link", { name: "Quota" }));
    await screen.findByRole("heading", { name: "Quota" });

    await user.click(screen.getByRole("button", { name: "Regenerate key" }));
    await user.click(screen.getByRole("button", { name: "Regenerate" }));

    expect(await screen.findByText("API key created")).toBeInTheDocument();
    expect(screen.getByText(/sk-clb-viewer-rotated/i)).toBeInTheDocument();
  });

  it("navigates to viewer settings and shows appearance controls", async () => {
    const user = userEvent.setup();
    window.history.replaceState({}, "", "/viewer");

    renderWithProviders(<App />);

    await user.type(await screen.findByLabelText("API Key"), "sk-clb-test-viewer");
    await user.click(screen.getByRole("button", { name: "Sign In" }));
    await screen.findByRole("heading", { name: "Dashboard" });

    await user.click(screen.getByRole("link", { name: "Settings" }));

    expect(await screen.findByRole("heading", { name: "Settings" })).toBeInTheDocument();
    expect(screen.getByText("Choose how the viewer portal looks.")).toBeInTheDocument();
    expect(screen.getByText("Appearance")).toBeInTheDocument();
    expect(screen.getByText("Theme")).toBeInTheDocument();
  });
});
