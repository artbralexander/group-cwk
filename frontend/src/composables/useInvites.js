import { ref } from "vue"
import { subscribeToNotifications } from "../services/notifications"

const invites = ref([])
const loadingInvites = ref(false)
const inviteError = ref("")
const acceptingInviteId = ref(null)
let unsubscribe = null

function addOrUpdateInvite(invite) {
  const existingIndex = invites.value.findIndex((item) => item.id === invite.id)
  if (existingIndex >= 0) {
    invites.value[existingIndex] = invite
  } else {
    invites.value = [invite, ...invites.value]
  }
}

async function fetchInvites() {
  loadingInvites.value = true
  inviteError.value = ""

  try {
    const res = await fetch("/api/invites", { credentials: "include" })
    if (!res.ok) {
      throw new Error("Unable to load invites")
    }
    invites.value = await res.json()
  } catch (err) {
    inviteError.value = err.message || "Failed to load invites"
    invites.value = []
  } finally {
    loadingInvites.value = false
  }
}

async function acceptInvite(inviteId) {
  acceptingInviteId.value = inviteId
  inviteError.value = ""
  try {
    const res = await fetch(`/api/invites/${inviteId}/accept`, {
      method: "POST",
      credentials: "include"
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail || "Unable to accept invite")
    }
    invites.value = invites.value.filter((invite) => invite.id !== inviteId)
    return await res.json()
  } catch (err) {
    inviteError.value = err.message || "Failed to accept invite"
    throw err
  } finally {
    acceptingInviteId.value = null
  }
}

function connectToInviteSocket() {
  if (unsubscribe || typeof window === "undefined") {
    return
  }
  unsubscribe = subscribeToNotifications("invite", (data) => {
    if (data) {
      addOrUpdateInvite(data)
    }
  })
}

export function useInvites() {
  return {
    invites,
    loadingInvites,
    inviteError,
    acceptingInviteId,
    fetchInvites,
    acceptInvite,
    connectToInviteSocket
  }
}
