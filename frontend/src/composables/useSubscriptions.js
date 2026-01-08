import { ref } from "vue"
import { subscribeToNotifications } from "../services/notifications"

let subscriptionsUnsubscribe = null

export function useSubscriptions() {
  const loading = ref(false)
  const error = ref("")

  async function request(url, options = {}) {
    loading.value = true
    error.value = ""
    try {
      const res = await fetch(url, { credentials: "include", ...options })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || "Request failed")
      }
      const text = await res.text()
      if (!text) {
        return null
      }
      return JSON.parse(text)
    } catch (err) {
      error.value = err.message || "Request failed"
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    list(groupId) {
      return request(`/api/groups/${groupId}/subscriptions`)
    },
    create(groupId, payload) {
      return request(`/api/groups/${groupId}/subscriptions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      })
    },
    update(groupId, subId, payload) {
      return request(`/api/groups/${groupId}/subscriptions/${subId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      })
    },
    remove(groupId, subId) {
      return request(`/api/groups/${groupId}/subscriptions/${subId}`, { method: "DELETE" })
    },
    pay(groupId, subId) {
      return request(`/api/groups/${groupId}/subscriptions/${subId}/pay`, { method: "POST" })
    },
    connectToSubscriptionNotifications(onChange) {
      if (subscriptionsUnsubscribe || typeof window === "undefined") {
        return
      }
      subscriptionsUnsubscribe = subscribeToNotifications("subscriptions_changed", (data) => {
        if (data?.group_id && typeof onChange === "function") {
          onChange(data.group_id, data)
        }
      })
    }
  }
}
