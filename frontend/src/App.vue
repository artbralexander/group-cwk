<template>
  <div>
    <nav :class="['navbar navbar-expand-lg border-bottom', isDarkMode ? 'navbar-dark bg-dark' : 'navbar-light bg-light']">
      <div class="container-fluid">
        <RouterLink class="navbar-brand fw-bold" to="/">
          SplitPay
        </RouterLink>

        <button
          class="navbar-toggler"
          type="button"
          aria-controls="navbarMain"
          :aria-expanded="showMobileNav"
          aria-label="Toggle navigation"
          @click="toggleNav"
        >
          <span class="navbar-toggler-icon"></span>
        </button>

<div :class="['collapse navbar-collapse', { show: showMobileNav }]" id="navbarMain">
          <ul class="navbar-nav me-auto mb-2 mb-lg-0">
            <li class="nav-item">
              <RouterLink class="nav-link" to="/" @click="closeMobileNav">Home</RouterLink>
            </li>
            <li class="nav-item" v-if="authLoaded && isAuthenticated">
              <RouterLink class="nav-link" to="/groups" @click="closeMobileNav">Groups</RouterLink>
            </li>
          </ul>

          <div
            class="d-flex align-items-start align-items-lg-center gap-2 flex-column flex-lg-row"
            v-if="authLoaded && isAuthenticated"
          >
            <RouterLink class="align-self-start align-self-lg-center small text-decoration-none" to="/settings" @click="closeMobileNav">
              {{ currentUser.username }}
            </RouterLink>
            <template v-if="confirmingLogout">
              <span class="small text-muted">Confirm logout?</span>
              <button class="btn btn-danger btn-sm w-100 w-lg-auto" @click="confirmLogout" type="button">
                Yes
              </button>
              <button class="btn btn-secondary btn-sm w-100 w-lg-auto" @click="cancelLogout" type="button">
                No
              </button>
            </template>
            <button
              v-else
              class="btn btn-outline-danger btn-sm w-100 w-lg-auto"
              @click="startLogoutConfirmation"
              type="button"
            >
              Logout
            </button>
          </div>
          <div class="d-flex gap-2 flex-column flex-sm-row w-100 w-sm-auto" v-else>
            <RouterLink to="/login" class="btn btn-outline-secondary btn-sm w-100 w-sm-auto" @click="closeMobileNav">
              Login
            </RouterLink>
            <RouterLink to="/register" class="btn btn-primary btn-sm w-100 w-sm-auto" @click="closeMobileNav">
              Sign up
            </RouterLink>
          </div>
        </div>
      </div>
    </nav>

    <!-- Page content -->
    <main class="container mt-4">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref, watch } from "vue"
import { RouterLink, RouterView, useRouter, useRoute } from "vue-router"
import { useAuth } from "./composables/useAuth"

const router = useRouter()
const route = useRoute()
const { currentUser, authLoaded, fetchCurrentUser, logout } = useAuth()

const isAuthenticated = computed(() => Boolean(currentUser.value))
const isDarkMode = ref(false)
const confirmingLogout = ref(false)
const showMobileNav = ref(false)

let removeColorSchemeListener

function applyTheme(isDark) {
  if (typeof document === "undefined") return
  const theme = isDark ? "dark" : "light"
  document.documentElement.setAttribute("data-bs-theme", theme)
  isDarkMode.value = isDark
}

function setupColorSchemeListener() {
  if (typeof window === "undefined" || !window.matchMedia) return

  const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)")
  applyTheme(mediaQuery.matches)

  const listener = (event) => applyTheme(event.matches)

  if (mediaQuery.addEventListener) {
    mediaQuery.addEventListener("change", listener)
    removeColorSchemeListener = () => mediaQuery.removeEventListener("change", listener)
  } else {
    mediaQuery.addListener(listener)
    removeColorSchemeListener = () => mediaQuery.removeListener(listener)
  }
}

onMounted(() => {
  fetchCurrentUser()
  setupColorSchemeListener()
})

onBeforeUnmount(() => {
  if (removeColorSchemeListener) {
    removeColorSchemeListener()
  }
})

function startLogoutConfirmation() {
  confirmingLogout.value = true
}

function cancelLogout() {
  confirmingLogout.value = false
}

async function confirmLogout() {
  await logout()
  confirmingLogout.value = false
  router.push("/")
}

function toggleNav() {
  showMobileNav.value = !showMobileNav.value
}

function closeMobileNav() {
  showMobileNav.value = false
}

watch(
  () => route.fullPath,
  () => {
    closeMobileNav()
  }
)
</script>
