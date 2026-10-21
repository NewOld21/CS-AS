<script setup lang="ts">
import { ref } from 'vue'
import OrbitMap from '../../shared/ui/OrbitMap.vue'
import BaseButton from '../../shared/ui/BaseButton.vue'
import FeatureDialog from '../../shared/ui/FeatureDialog.vue'
const feature = ref<'quiz' | 'chat' | null>(null)
</script>
<template>
  <main id="main" tabindex="-1">
    <section id="explore" class="hero">
      <div class="hero-copy">
        <div class="hero-eyebrow">
          <span class="status-dot"></span><span class="mono">A NEW WAY TO EXPLORE CS</span
          ><span class="version-tag mono">VOL. 01</span>
        </div>
        <h1>
          지식의 궤도를,<br /><span>나만의 속도로.</span
          ><span class="title-spark" aria-hidden="true">✳</span>
        </h1>
        <p class="hero-description">CS를 공부하고, 퀴즈로 확인하고,<br />AI로 다시 이해하다.</p>
        <p class="hero-subcopy">
          외우는 공부를 넘어, 연결되는 이해로.<br />당신의 다음 물음표에서 탐험이 시작됩니다.
        </p>
        <RouterLink to="/signup" class="button button--primary hero-cta"
          >CS 학습 시작하기<span class="button-arrow" aria-hidden="true">↗</span></RouterLink
        >
        <div class="hero-actions">
          <BaseButton variant="quiet" @click="feature = 'quiz'"
            >퀴즈 풀기 <span aria-hidden="true">↗</span></BaseButton
          ><span aria-hidden="true">/</span
          ><BaseButton variant="quiet" @click="feature = 'chat'"
            >AI에게 질문하기 <span aria-hidden="true">↗</span></BaseButton
          >
        </div>
        <p class="availability-note">
          <span class="tiny-dot" aria-hidden="true"></span>가입·로그인 이용 가능 · 학습 기능은 준비
          중이에요
        </p>
        <a href="#journey" class="scroll-cue mono"
          ><span aria-hidden="true">↓</span> SCROLL TO DISCOVER</a
        >
      </div>
      <OrbitMap />
    </section>
    <section id="journey" class="journey-section" aria-labelledby="journey-title">
      <div class="section-heading">
        <div>
          <p class="eyebrow">SMALL QUESTIONS. BIG CONNECTIONS.</p>
          <h2 id="journey-title">하나의 질문에서,<br />이해가 이어지는 여정.</h2>
        </div>
        <p>
          퀴즈에서 발견한 빈틈을 질문으로 채우고,<br />다시 풀며 내 것으로 만드는 학습을 준비합니다.
        </p>
      </div>
      <ol class="journey-track">
        <li>
          <span class="journey-index mono">01 / CHECK</span>
          <div class="journey-glyph" aria-hidden="true">[ ? ]</div>
          <h3>먼저, 확인하고.</h3>
          <p>분야별 CS 퀴즈를 통해<br />알고 있는 것과 궁금한 것을 발견해요.</p>
          <span class="coming-label">퀴즈 · 준비 중</span>
        </li>
        <li>
          <span class="journey-index mono">02 / ASK</span>
          <div class="journey-glyph" aria-hidden="true">&gt;_</div>
          <h3>깊이, 질문하고.</h3>
          <p>왜 틀렸는지, 무엇이 다른지.<br />출처가 있는 답변으로 이해를 넓혀요.</p>
          <span class="coming-label">AI 질문 · 준비 중</span>
        </li>
        <li>
          <span class="journey-index mono">03 / CONNECT</span>
          <div class="journey-glyph" aria-hidden="true">↻</div>
          <h3>다시, 연결해요.</h3>
          <p>관련 문제와 오답 복습으로<br />흩어진 지식을 나만의 맥락으로 엮어요.</p>
          <span class="coming-label">학습 기록 · 준비 중</span>
        </li>
      </ol>
      <div class="journey-bottom">
        <span class="mono">EVERY QUESTION IS A NEW COORDINATE.</span
        ><RouterLink to="/signup">나의 여정 준비하기 <span aria-hidden="true">↗</span></RouterLink>
      </div>
    </section>
    <FeatureDialog :feature="feature" @close="feature = null" />
  </main>
</template>
