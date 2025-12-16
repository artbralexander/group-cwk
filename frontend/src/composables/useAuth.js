import { ref } from "vue"

const currentUser = ref(null)
const authLoaded = ref(false)

async function fetchCurrentUser() {
  try {
    const res = await fetch("/api/auth/me", {
      method: "GET",
      credentials: "include"
    })

    if (!res.ok) {
      throw new Error("Not authenticated")
    }

    currentUser.value = await res.json()
  } catch {
    currentUser.value = null
  } finally {
    authLoaded.value = true
  }
}

async function logout() {
  await fetch("/api/auth/logout", {
    method: "POST",
    credentials: "include"
  })

  currentUser.value = null
}

export function useAuth() {
  return {
    currentUser,
    authLoaded,
    fetchCurrentUser,
    logout
  }
}
