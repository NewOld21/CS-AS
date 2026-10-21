<script setup lang="ts">
import { ref } from 'vue'
const active = ref(0)
const paused = ref(false)
const concepts = [
  {
    id: 'os',
    code: '01',
    name: '운영체제',
    en: 'OPERATING SYSTEM',
    glyph: '⌘',
    description: '프로세스에서 메모리까지. 컴퓨터가 일하는 방식을 이해해요.',
  },
  {
    id: 'db',
    code: '02',
    name: '데이터베이스',
    en: 'DATABASE',
    glyph: '▤',
    description: '데이터가 쌓이고 연결되는 원리. 인덱스와 트랜잭션을 탐구해요.',
  },
  {
    id: 'network',
    code: '03',
    name: '네트워크',
    en: 'NETWORK',
    glyph: '⤧',
    description: '작은 패킷이 연결하는 세상. 요청이 도착하는 여정을 따라가요.',
  },
  {
    id: 'algorithm',
    code: '04',
    name: '알고리즘',
    en: 'ALGORITHM',
    glyph: '{ }',
    description: '더 나은 풀이로 가는 길. 문제를 나누고, 규칙을 발견해요.',
  },
  {
    id: 'structure',
    code: '05',
    name: '자료구조',
    en: 'DATA STRUCTURE',
    glyph: '⠿',
    description: '생각을 담는 여러 가지 그릇. 데이터의 모양과 쓰임을 살펴봐요.',
  },
]
</script>
<template>
  <section class="orbit-map" aria-label="CS 개념 탐색 지도">
    <div class="map-caption">
      <span class="mono">THE CS UNIVERSE</span
      ><button :aria-pressed="paused" class="motion-control" @click="paused = !paused">
        {{ paused ? '움직임 재생' : '움직임 멈춤' }}
        <span aria-hidden="true">{{ paused ? '▷' : 'Ⅱ' }}</span>
      </button>
    </div>
    <div class="map-world" :class="{ 'is-paused': paused }">
      <div class="world-grid" aria-hidden="true"></div>
      <svg class="orbit-tracks" viewBox="0 0 620 560" fill="none" aria-hidden="true">
        <ellipse cx="310" cy="270" rx="251" ry="211" transform="rotate(-22 310 270)" />
        <ellipse cx="310" cy="270" rx="195" ry="156" transform="rotate(30 310 270)" />
        <path d="M104 173 310 270 454 110M310 270l195 124M310 270l-90 177M310 270 65 310" />
        <circle cx="310" cy="270" r="113" />
      </svg>
      <span v-for="n in 10" :key="n" class="map-star" :class="`map-star--${n}`" aria-hidden="true"
        >+</span
      >
      <div class="map-core" aria-hidden="true">
        <div class="core-halo"></div>
        <span class="core-label">CS<span>/</span>AS</span><small>CONNECT THE DOTS</small>
      </div>
      <button
        v-for="(concept, index) in concepts"
        :key="concept.id"
        class="concept-node"
        :class="[`concept-node--${concept.id}`, { 'is-active': active === index }]"
        :aria-pressed="active === index"
        :aria-label="`${concept.name} 개념 살펴보기`"
        @click="active = index"
      >
        <span class="node-object" aria-hidden="true"
          ><span class="node-glyph">{{ concept.glyph }}</span
          ><span class="node-base"></span><i></i
        ></span>
        <span class="node-name"
          ><small>{{ concept.code }}</small
          >{{ concept.name }}<span aria-hidden="true">↗</span></span
        >
      </button>
      <div class="map-coordinate mono" aria-hidden="true">X: LEARN<br />Y: UNDERSTAND</div>
      <span class="map-note mono" aria-hidden="true"
        >NO WRONG TURNS.<br />JUST NEW CONNECTIONS.</span
      >
    </div>
    <div class="concept-detail" aria-live="polite" aria-atomic="true">
      <span class="concept-number mono">{{ concepts[active]!.code }}<span>/05</span></span>
      <div>
        <span class="eyebrow">{{ concepts[active]!.en }}</span>
        <p>{{ concepts[active]!.description }}</p>
      </div>
      <span class="detail-star" aria-hidden="true">✳</span>
    </div>
  </section>
</template>
