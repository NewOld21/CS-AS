<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import BrandMark from '../shared/ui/BrandMark.vue'
import { useAuth } from '../domains/auth/store'
const auth = useAuth()
const route = useRoute()
const menuOpen = ref(false)
const menuToggle = ref<HTMLButtonElement>()
function closeMenu() {
  menuOpen.value = false
  menuToggle.value?.focus()
}
function focusMain() {
  document.querySelector<HTMLElement>('main')?.focus({ preventScroll: true })
}
watch(
  () => route.fullPath,
  () => {
    menuOpen.value = false
  },
)
</script>
<template>
  <a class="skip-link" href="#main">본문으로 건너뛰기</a>
  <div class="site-shell">
    <header class="site-header">
      <BrandMark />
      <button
        ref="menuToggle"
        class="menu-toggle"
        :aria-expanded="menuOpen"
        aria-controls="site-nav"
        @click="menuOpen = !menuOpen"
        @keydown.esc="closeMenu"
      >
        {{ menuOpen ? '닫기 ✕' : '메뉴 ☰' }}
      </button>
      <nav
        id="site-nav"
        aria-label="주 메뉴"
        :class="{ 'is-open': menuOpen }"
        @keydown.esc="closeMenu"
      >
        <RouterLink to="/#explore">학습 지도</RouterLink
        ><RouterLink to="/#journey">학습 여정</RouterLink>
        <RouterLink v-if="auth.user" to="/learn">퀴즈 · AS</RouterLink
        ><span class="nav-divider" aria-hidden="true"></span
        ><RouterLink v-if="auth.user" to="/account">내 계정</RouterLink
        ><RouterLink v-else to="/login">로그인</RouterLink
        ><RouterLink to="/signup" class="nav-join"
          >계정 만들기 <span aria-hidden="true">↗</span></RouterLink
        >
      </nav>
    </header>
    <RouterView v-slot="{ Component }"
      ><Transition name="page" mode="out-in" @after-enter="focusMain"
        ><component :is="Component" :key="route.path" /></Transition
    ></RouterView>
    <footer class="site-footer">
      <span class="mono">CS/AS <span class="muted">— ASK. UNDERSTAND. CONNECT.</span></span
      ><span>어제의 물음표가, 오늘의 마침표가 되도록.</span
      ><a href="/#journey">서비스 안내 <span aria-hidden="true">↗</span></a>
    </footer>
  </div>
</template>
