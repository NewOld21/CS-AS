<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from './store'
import { errorMessage } from './validation'
import BaseButton from '../../shared/ui/BaseButton.vue'
import StatusMessage from '../../shared/ui/StatusMessage.vue'
const auth = useAuth()
const router = useRouter()
const loading = ref(true)
const busy = ref(false)
const failure = ref('')
async function load() {
  loading.value = true
  failure.value = ''
  try {
    await auth.restore()
    if (!auth.user) await router.replace('/login')
  } catch (error) {
    failure.value = errorMessage(error)
  } finally {
    loading.value = false
  }
}
async function logout() {
  busy.value = true
  failure.value = ''
  try {
    await auth.logout()
    await router.replace('/login')
  } catch (error) {
    failure.value = errorMessage(error)
  } finally {
    busy.value = false
  }
}
onMounted(load)
</script>
<template>
  <main id="main" class="account-page" tabindex="-1">
    <p class="eyebrow">YOUR BASE CAMP</p>
    <h1>나의 연결 지점.</h1>
    <p class="hero-subcopy">내 계정 정보를 확인하고 다음 탐험을 준비하세요.</p>
    <div v-if="loading" class="account-panel" role="status">
      <span class="spinner" aria-hidden="true"></span>계정 정보를 불러오고 있어요.
    </div>
    <template v-else
      ><StatusMessage v-if="failure" kind="error">{{ failure }}</StatusMessage
      ><BaseButton v-if="!auth.user" variant="secondary" @click="load">다시 불러오기</BaseButton>
      <section v-if="auth.user" class="account-panel" aria-labelledby="account-title">
        <div class="account-avatar" aria-hidden="true">
          {{ (auth.user.nickname || auth.user.email).slice(0, 1).toUpperCase() }}
        </div>
        <div>
          <h2 id="account-title">{{ auth.user.nickname || '탐험가' }}님, 연결됐어요.</h2>
          <p>{{ auth.user.email }}</p>
          <span class="account-session"><span class="status-dot"></span>로그인 상태</span>
        </div>
        <BaseButton variant="secondary" :loading="busy" @click="logout"
          >로그아웃 <span aria-hidden="true">↗</span></BaseButton
        >
      </section>
      <section class="account-next">
        <span class="eyebrow">NEXT CHAPTER</span>
        <h2>학습 기록이 쌓일 공간을 준비하고 있어요.</h2>
        <p>
          퀴즈, AI 질문, 오답 복습은 아직 준비 중입니다.<br />지금은 계정 기능을 이용하고, 학습
          지도에서 CS 분야를 살펴볼 수 있어요.
        </p>
        <RouterLink to="/#explore" class="button button--primary">학습 지도 살펴보기 ↗</RouterLink>
      </section></template
    >
  </main>
</template>
