<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'

const HI_LINK = 'https://meeting.ssafy.com/s14public/messages/@py9245'
const MOBILE_WIDTH = 992

const isMobile = ref(false)
const isOpen = ref(true)

const checkViewport = () => {
  isMobile.value = window.innerWidth < MOBILE_WIDTH
  if (!isMobile.value) {
    isOpen.value = true
  }
}

const toggle = () => {
  isOpen.value = !isOpen.value
}

onMounted(() => {
  checkViewport()
  window.addEventListener('resize', checkViewport)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkViewport)
})

const containerClasses = computed(() => ({
  'hi-sidebar': true,
  'hi-sidebar--closed': isMobile.value && !isOpen.value,
}))

const toggleLabel = computed(() => (isOpen.value ? '닫기' : '"HI" 인사하기'))
</script>

<template>
  <aside :class="containerClasses">
    <button v-if="isMobile" class="hi-sidebar__toggle btn btn-outline-secondary btn-sm" type="button" @click="toggle">
      {{ toggleLabel }}
    </button>
    <div v-show="!isMobile || isOpen">
      <div class="hi-sidebar__badge">제작자</div>
      <h3 class="hi-sidebar__title">"HI" 인사하기</h3>
      <p class="hi-sidebar__text">서비스 제작자(py9245)에게 응원의 인사를 전하고 궁금한 점을 바로 남겨보세요.</p>
      <a class="hi-sidebar__cta btn btn-success btn-sm" :href="HI_LINK" target="_blank" rel="noopener">
        메세지 보내기
      </a>
    </div>
  </aside>
</template>
