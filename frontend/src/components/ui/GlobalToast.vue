<script setup lang="ts">
import { useUI } from "@/composables/useUI";

const { toastState } = useUI();
</script>

<template>
  <Transition name="toast-pop">
    <div v-if="toastState.show" class="toast-wrapper">
      <div 
        class="toast-pill" 
        :class="toastState.type"
      >
        <div class="toast-icon">
          <svg v-if="toastState.type === 'success'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>
          <svg v-else-if="toastState.type === 'error'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
        </div>
        <span class="toast-text">{{ toastState.message }}</span>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.toast-wrapper {
  position: fixed;
  bottom: 32px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  pointer-events: none;
}

.toast-pill {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  border-radius: 99px;
  background: var(--bg-panel);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-float);
  color: var(--txt-primary);
  min-width: 300px;
  justify-content: center;
}

/* Variants */
.toast-pill.success { border-color: var(--success); background: radial-gradient(circle at center, var(--success-bg), var(--bg-panel)); }
.toast-pill.success .toast-icon { color: var(--success); }

.toast-pill.error { border-color: var(--error); background: radial-gradient(circle at center, var(--error-bg), var(--bg-panel)); }
.toast-pill.error .toast-icon { color: var(--error); }

.toast-text { font-size: 14px; font-weight: 500; }

/* Animation */
.toast-pop-enter-active, .toast-pop-leave-active { transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
.toast-pop-enter-from, .toast-pop-leave-to { opacity: 0; transform: translate(-50%, 20px) scale(0.9); }
</style>
