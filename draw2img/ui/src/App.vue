<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <header>
    <h1 style="margin:0 0 .5em 0;">Draw2Img</h1>
    <!-- <img alt="logo" class="logo" src="@/assets/logo.svg" width="125" height="125" /> -->
    <!-- <div class="wrapper">
      <nav>
        <RouterLink to="/">Home</RouterLink>
      </nav>
    </div> -->
  </header>
  <RouterView />
</template>