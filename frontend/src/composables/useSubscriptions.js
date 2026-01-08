import { ref } from "vue"
import { subscribeToNotifications } from "../services/notifications"

export function useSubscriptions() {
  const loading = ref(false)
  const error = ref("")
  let subscriptionUnsubscribe = null

  async function request(url, options = {}) {
    loading.value = true
    error.value = ""
    try {
      const res = await fetch(url, { credentials: "include", ...options })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || "Request failed")
      }
      return await res.json()
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
    connectToSubscriptionNotifications(onChange) {
      if (subscriptionUnsubscribe || typeof window === "undefined") {
        return
      }
      subscriptionUnsubscribe = subscribeToNotifications("subscriptions_changed", (data) => {
        if (data?.group_id && typeof onChange === "function") {
          onChange(data.group_id)
        }
      })
    },
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
    }
  }
}
