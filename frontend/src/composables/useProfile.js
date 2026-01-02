import { ref } from "vue"

const summary = ref(null)
const loadingSummary = ref(false)
const summaryError = ref("")

async function fetchSpendingSummary() {
  loadingSummary.value = true
  summaryError.value = ""

  try {
    const res = await fetch("/api/profile/spending-summary", {
      credentials: "include"
    })

    if (!res.ok) {
      throw new Error("Unable to load spending summary")
    }

    summary.value = await res.json()
  } catch (err) {
    summaryError.value = err.message || "Failed to load spending summary"
    summary.value = null
  } finally {
    loadingSummary.value = false
  }
}

export function useProfile() {
  return {
    summary,
    loadingSummary,
    summaryError,
    fetchSpendingSummary
  }
}