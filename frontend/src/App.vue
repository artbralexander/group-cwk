<template>
  <div>
    <nav class="navbar navbar-expand-lg navbar-light bg-light border-bottom">
      <div class="container-fluid">
        <RouterLink class="navbar-brand fw-bold" to="/">
          SplitPay
        </RouterLink>

        <button
          class="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#navbarMain"
        >
          <span class="navbar-toggler-icon"></span>
        </button>

        <div class="collapse navbar-collapse" id="navbarMain">
          <ul class="navbar-nav me-auto mb-2 mb-lg-0">
            <li class="nav-item">
              <RouterLink class="nav-link" to="/">Home</RouterLink>
            </li>
            <li class="nav-item">
              <RouterLink class="nav-link" to="/groups">Groups</RouterLink>
            </li>
          </ul>

          <div class="d-flex gap-2">
            <RouterLink to="/login" class="btn btn-outline-secondary btn-sm">
              Login
            </RouterLink>
            <RouterLink to="/register" class="btn btn-primary btn-sm">
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
import { RouterLink, RouterView } from "vue-router"
</script>
