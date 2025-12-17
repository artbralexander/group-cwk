<template>
  <div class="container py-5">
    <div class="row justify-content-center">
      <div class="col-md-6 col-lg-5">
        <div class="card shadow-sm">
          <div class="card-body">
            <h3 class="card-title mb-4 text-center">Login</h3>

            <form @submit.prevent="login">
              <div class="mb-3">
                <label for="username" class="form-label">Username</label>
                <input
                  id="username"
                  v-model="form.username"
                  type="text"
                  class="form-control"
                  required
                  autofocus
                />
              </div>

              <div class="mb-3">
                <label for="password" class="form-label">Password</label>
                <input
                  id="password"
                  v-model="form.password"
                  type="password"
                  class="form-control"
                  required
                />
              </div>

              <div v-if="error" class="alert alert-danger py-2">
                {{ error }}
              </div>

              <button
                type="submit"
                class="btn btn-primary w-100"
                :disabled="loading"
              >
                <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                Login
              </button>
            </form>

            <hr class="my-4" />

            <div class="text-center">
              <small class="text-muted">
                Don’t have an account?
                <RouterLink to="/register">Sign up</RouterLink>
              </small>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue"
import { useRouter, useRoute, RouterLink } from "vue-router"
import { useAuth } from "../composables/useAuth"

const router = useRouter()
const route = useRoute()
const { fetchCurrentUser } = useAuth()

const form = reactive({
  username: "",
  password: ""
})

const loading = ref(false)
const error = ref("")

async function login() {
  loading.value = true
  error.value = ""

  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(form)
    })

    if (!res.ok) {
      throw new Error("Invalid username or password")
    }

    await fetchCurrentUser()

    const redirectTo = route.query.redirect || "/groups"
    router.push(redirectTo)
  } catch (err) {
    error.value = err.message || "Login failed"
  } finally {
    loading.value = false
  }
}
</script>
