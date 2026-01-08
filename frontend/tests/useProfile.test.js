import { describe, it, expect, vi } from "vitest"
import { useProfile } from "../src/composables/useProfile"

describe("useProfile", () => {
  it("fetches spending summary from API", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            groups: [],
            overall_paid: 0,
            overall_owed: 0,
          }),
      })
    )

    const { fetchSpendingSummary, spendingSummary } = useProfile()

    await fetchSpendingSummary()

    expect(fetch).toHaveBeenCalled()
    expect(spendingSummary.value).toBeTruthy()
  })
})
