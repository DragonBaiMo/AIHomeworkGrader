<script setup lang="ts">
import { useUI } from "@/shared/composables/useUI";

const { toasts } = useUI();
</script>

<template>
  <TransitionGroup name="toast-spring" tag="div" class="toast-wrapper">
    <div 
      v-for="toast in toasts" 
      :key="toast.id" 
      class="toast-capsule glass-morphism" 
      :class="toast.type"
    >
      <div class="toast-icon-box">
        <svg v-if="toast.type === 'success'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
        <svg v-else-if="toast.type === 'error'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
        <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
      </div>
      <span class="toast-message">{{ toast.message }}</span>
    </div>
  </TransitionGroup>
</template>

<style scoped>
.toast-wrapper {
  position: fixed;
  bottom: 48px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10000;
  pointer-events: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.toast-capsule {
  pointer-events: auto;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px 12px 14px;
  border-radius: 99px;
  background: var(--bg-popover);
  border: 1px solid var(--border-light);
  box-shadow: 
    0 10px 40px -10px rgba(0,0,0,0.3),
    0 0 0 1px rgba(255,255,255,0.05) inset;
  color: var(--txt-primary);
  min-width: 300px;
  max-width: 480px;
  backdrop-filter: blur(20px);
  will-change: transform, opacity;
}

.toast-icon-box {
  display: flex; align-items: center; justify-content: center;
  width: 28px; height: 28px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* Status Colors */
.toast-capsule.success .toast-icon-box {
  background: var(--success); color: #fff;
  box-shadow: 0 0 12px var(--success-bg);
}
.toast-capsule.error .toast-icon-box {
  background: var(--error); color: #fff;
  box-shadow: 0 0 12px var(--error-bg);
}
.toast-capsule.info .toast-icon-box {
  background: var(--txt-tertiary); color: #fff;
}

.toast-message {
  font-size: 13px;
  font-weight: 500;
  line-height: 1.4;
  letter-spacing: 0.01em;
}

/* Animation */
.toast-spring-enter-active, .toast-spring-leave-active {
  transition: opacity 0.4s cubic-bezier(0.19, 1, 0.22, 1), transform 0.4s cubic-bezier(0.19, 1, 0.22, 1);
}
.toast-spring-enter-from, .toast-spring-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(24px) scale(0.9);
}
</style>
