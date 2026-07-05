import { describe, it, expect } from "vitest";
import { formatApiError } from "../utils/apiError";

describe("formatApiError", () => {
  it("returns fallback when detail is missing", () => {
    expect(formatApiError(undefined, "Failed")).toBe("Failed");
  });

  it("returns string detail as-is", () => {
    expect(formatApiError("Bad request", "Failed")).toBe("Bad request");
  });

  it("formats validation error arrays", () => {
    const detail = [{ msg: "Password too short" }, { msg: "Missing digit" }];
    expect(formatApiError(detail, "Failed")).toBe(
      "Password too short. Missing digit"
    );
  });
});
