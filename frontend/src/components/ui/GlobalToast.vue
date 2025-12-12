<script setup lang="ts">
import { useUI } from "@/composables/useUI";

const { toastState } = useUI();
</script>

<template>
  <Transition name="toast-spring">
    <div v-if="toastState.show" class="toast-wrapper">
      <div 
        class="toast-capsule glass-morphism" 
        :class="toastState.type"
      >
        <div class="toast-icon-box">
          <svg v-if="toastState.type === 'success'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
          <svg v-else-if="toastState.type === 'error'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
        </div>
        <span class="toast-message">{{ toastState.message }}</span>
      </div>
    </div>
  </Transition>
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
  justify-content: center;
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
  transition: all 0.4s cubic-bezier(0.19, 1, 0.22, 1);
}
.toast-spring-enter-from, .toast-spring-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(24px) scale(0.9);
}
</style>
