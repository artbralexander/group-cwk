let socket = null
const listeners = new Map()

function getWebSocketUrl() {
  if (typeof window === "undefined") return ""
  const protocol = window.location.protocol === "https:" ? "wss" : "ws"
  return `${protocol}://${window.location.host}/ws/notifications`
}

function ensureSocket() {
  if (socket || typeof window === "undefined") {
    return
  }

  socket = new WebSocket(getWebSocketUrl())

  socket.addEventListener("message", (event) => {
    try {
      const payload = JSON.parse(event.data)
      if (payload?.type && listeners.has(payload.type)) {
        const handlers = listeners.get(payload.type)
        handlers.forEach((handler) => {
          try {
            handler(payload.data, payload)
          } catch {
            // ignore listener errors to keep socket alive
          }
        })
      }
    } catch {
      // ignore malformed payloads
    }
  })

  socket.addEventListener("close", () => {
    socket = null
    if (listeners.size > 0) {
      setTimeout(ensureSocket, 1000)
    }
  })
}

export function subscribeToNotifications(type, handler) {
  if (typeof window === "undefined") {
    return () => {}
  }

  if (!listeners.has(type)) {
    listeners.set(type, new Set())
  }
  const handlers = listeners.get(type)
  handlers.add(handler)

  ensureSocket()

  return () => {
    handlers.delete(handler)
    if (handlers.size === 0) {
      listeners.delete(type)
    }
  }
}
