import { describe, expect, it } from "vitest";
import { demoCases, demoEvents } from "./demo";

describe("officer dashboard first vertical slice", () => {
  it("keeps the case and score event joined by the shared event id", () => {
    const firstCase = demoCases[0];
    const event = demoEvents.find((item) => item.event_id === firstCase.event_id);
    expect(event).toBeDefined();
    expect(event?.band).toBe(firstCase.band);
    expect(firstCase.status).toBe("new");
  });
});
