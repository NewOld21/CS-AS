<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from './store'
import { validate, errorMessage } from './validation'
import BaseButton from '../../shared/ui/BaseButton.vue'
import FormField from '../../shared/ui/FormField.vue'
import StatusMessage from '../../shared/ui/StatusMessage.vue'
const route = useRoute()
const router = useRouter()
const auth = useAuth()
const signup = computed(() => route.path === '/signup')
const email = ref('')
const password = ref('')
const nickname = ref('')
const errors = ref<Record<string, string>>({})
const failure = ref('')
const busy = ref(false)
const success = ref(false)
const showPassword = ref(false)
async function submit() {
  if (busy.value) return
  errors.value = validate(email.value, password.value, signup.value ? nickname.value : undefined)
  failure.value = ''
  if (Object.keys(errors.value).length) {
    document.getElementById(Object.keys(errors.value)[0]!)?.focus()
    return
  }
  busy.value = true
  try {
    if (signup.value) {
      await auth.signup(email.value.trim(), password.value, nickname.value.trim())
      success.value = true
      password.value = ''
    } else {
      await auth.login(email.value.trim(), password.value)
      password.value = ''
      await router.push('/account')
    }
  } catch (error) {
    failure.value = errorMessage(error)
  } finally {
    busy.value = false
  }
}
</script>
<template>
  <main id="main" class="auth-layout" tabindex="-1">
    <section class="auth-story">
      <RouterLink to="/" class="back-link">← 탐험 지도로 돌아가기</RouterLink>
      <p class="eyebrow">{{ signup ? 'YOUR FIRST COORDINATE' : 'WELCOME BACK, EXPLORER' }}</p>
      <h1>
        {{ signup ? '모든 이해는,' : '다시 만난,' }}<br /><span>{{
          signup ? '질문에서 시작해요.' : '우리의 학습 궤도.'
        }}</span>
      </h1>
      <p>정답을 아는 것에서 한 걸음 더.<br />왜 그런지 이해하는 즐거움을 함께 발견해요.</p>
      <div class="auth-constellation" aria-hidden="true">
        <div class="constellation-ring"></div>
        <span class="constellation-main">&gt;_</span><span class="constellation-small">?</span
        ><span class="constellation-small">{ }</span
        ><span class="constellation-caption mono">ASK → UNDERSTAND → CONNECT</span>
      </div>
    </section>
    <section class="auth-card" :aria-labelledby="success ? 'success-title' : 'auth-title'">
      <template v-if="success"
        ><span class="success-mark" aria-hidden="true">✓</span>
        <p class="eyebrow">FIRST CONNECTION MADE</p>
        <h2 id="success-title">첫 연결이 만들어졌어요.</h2>
        <StatusMessage kind="success">가입이 완료됐어요. 이제 로그인할 수 있습니다.</StatusMessage>
        <p class="card-description">
          가입한 이메일과 비밀번호로 로그인해 주세요.<br />회원가입만으로 로그인되지는 않아요.
        </p>
        <RouterLink to="/login" class="button button--primary full-width"
          >로그인하러 가기 <span aria-hidden="true">↗</span></RouterLink
        ></template
      >
      <template v-else
        ><div class="auth-card-top">
          <span class="mono">BASE CAMP / {{ signup ? 'SIGN UP' : 'LOG IN' }}</span
          ><span class="tiny-dot" aria-hidden="true"></span>
        </div>
        <h2 id="auth-title">{{ signup ? '새로운 여정을 시작해요.' : '다시 만나 반가워요.' }}</h2>
        <p class="card-description">
          {{
            signup ? '나만의 학습 공간을 위한 첫 번째 단계.' : '당신의 다음 질문이 기다리고 있어요.'
          }}
        </p>
        <form novalidate :aria-busy="busy" @submit.prevent="submit">
          <fieldset :disabled="busy" class="auth-fields">
            <legend class="sr-only">{{ signup ? '회원가입 정보' : '로그인 정보' }}</legend>
            <FormField
              id="email"
              v-model="email"
              label="이메일"
              type="email"
              autocomplete="email"
              required
              :maxlength="254"
              :error="errors.email"
            />
            <div class="password-field">
              <FormField
                id="password"
                v-model="password"
                label="비밀번호"
                :type="showPassword ? 'text' : 'password'"
                :autocomplete="signup ? 'new-password' : 'current-password'"
                required
                :maxlength="128"
                :error="errors.password"
                :hint="signup ? '12자 이상 · 영문 기준 최대 72자' : undefined"
              /><button
                type="button"
                class="password-toggle"
                :aria-pressed="showPassword"
                @click="showPassword = !showPassword"
              >
                비밀번호 {{ showPassword ? '숨기기' : '보기' }}
              </button>
            </div>
            <FormField
              v-if="signup"
              id="nickname"
              v-model="nickname"
              label="닉네임"
              autocomplete="nickname"
              :maxlength="40"
              :error="errors.nickname"
            />
          </fieldset>
          <StatusMessage v-if="failure" kind="error">{{ failure }}</StatusMessage
          ><BaseButton class="full-width" type="submit" :loading="busy"
            >{{ busy ? '잠시만 기다려 주세요' : signup ? '내 계정 만들기' : '로그인하기'
            }}<span v-if="!busy" aria-hidden="true">↗</span></BaseButton
          >
        </form>
        <p class="auth-switch">
          {{ signup ? '이미 계정이 있나요?' : '아직 계정이 없나요?' }}
          <RouterLink :to="signup ? '/login' : '/signup'"
            >{{ signup ? '로그인' : '회원가입' }} ↗</RouterLink
          >
        </p>
        <div class="auth-trust">
          <span aria-hidden="true">◇</span> 비밀번호 원문은 저장하지 않아요.
        </div>
      </template>
    </section>
  </main>
</template>
