import { ref } from "vue"

const summary = ref(null)
const loadingSummary = ref(false)
const summaryError = ref("")
const summaryText = ref("")
const loadingSummaryText = ref(false)
const summaryTextError = ref("")

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

async function fetchSpendingSummaryText() {
  loadingSummaryText.value = true
  summaryTextError.value = ""
  summaryText.value = ""

  try {
    const res = await fetch("/api/profile/spending-summary-text", {
      credentials: "include"
    })

    if (!res.ok) {
      throw new Error("Unable to generate summary")
    }

    const data = await res.json()
    summaryText.value = data.summary || ""
  } catch (err) {
    summaryTextError.value = err.message || "Failed to generate summary"
  } finally {
    loadingSummaryText.value = false
  }
}

export function useProfile() {
  return {
    summary,
    loadingSummary,
    summaryError,
    fetchSpendingSummary,

    summaryText,
    loadingSummaryText,
    summaryTextError,
    fetchSpendingSummaryText
  }
}