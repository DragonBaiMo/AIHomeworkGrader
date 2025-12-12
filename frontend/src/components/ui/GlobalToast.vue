<script setup lang="ts">
import { useUI } from "@/composables/useUI";

const { toasts, removeToast } = useUI();

const Icons = {
  success: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>`,
  error: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`,
  info: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`,
  warning: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`,
};
</script>

<template>
  <div class="toast-container">
    <TransitionGroup name="toast-pop">
      <div 
        v-for="toast in toasts" 
        :key="toast.id" 
        class="toast-item glass"
        :class="toast.type"
        @click="removeToast(toast.id)"
      >
        <div class="icon-box" v-html="Icons[toast.type]"></div>
        <span class="message">{{ toast.message }}</span>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toast-container {
  position: fixed;
  top: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 12px;
  pointer-events: none; /* Let clicks pass through gaps */
}

.toast-item {
  pointer-events: auto;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 20px;
  border-radius: 99px;
  min-width: 300px;
  max-width: 90vw;
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
  cursor: pointer;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.1);
  color: var(--txt-primary);
  background: rgba(20, 20, 23, 0.85); /* Default dark glass */
}

/* Light mode support via CSS variables if setup, or direct override */
[data-theme="light"] .toast-item {
  background: rgba(255, 255, 255, 0.9);
  border-color: rgba(0,0,0,0.05);
  color: #18181b;
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}

/* Variants */
.toast-item.success { border-left: 3px solid var(--success); }
.toast-item.success .icon-box { color: var(--success); }

.toast-item.error { border-left: 3px solid var(--error); }
.toast-item.error .icon-box { color: var(--error); }

.toast-item.warning { border-left: 3px solid #f59e0b; }
.toast-item.warning .icon-box { color: #f59e0b; }

.toast-item.info { border-left: 3px solid var(--brand); }
.toast-item.info .icon-box { color: var(--brand); }

.message {
  font-size: 14px;
  font-weight: 500;
}

/* Animation */
.toast-pop-enter-active,
.toast-pop-leave-active {
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
.toast-pop-enter-from {
  opacity: 0;
  transform: translateY(-20px) scale(0.9);
}
.toast-pop-leave-to {
  opacity: 0;
  transform: translateY(-20px) scale(0.9);
}
</style>