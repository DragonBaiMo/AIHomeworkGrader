<script setup lang="ts">
import { useUI } from "@/composables/useUI";

const { modalState, closeModal } = useUI();

function handleConfirm() {
  if (modalState.options?.onConfirm) {
    modalState.options.onConfirm();
  }
  closeModal();
}
</script>

<template>
  <Transition name="modal-pop">
    <div v-if="modalState.isOpen && modalState.options" class="modal-backdrop" @click.self="closeModal">
      <div class="modal-card">
        <div class="modal-header">
          <h3 class="modal-title">{{ modalState.options.title }}</h3>
        </div>
        <div class="modal-body">
          <p class="modal-text">{{ modalState.options.content }}</p>
        </div>
        
        <div class="modal-footer">
          <button class="bento-btn ghost" @click="closeModal">
            {{ modalState.options.cancelText || '取消' }}
          </button>
          <button 
            class="bento-btn" 
            :class="modalState.options.type === 'danger' ? 'danger' : 'primary'"
            @click="handleConfirm"
          >
            {{ modalState.options.confirmText || '确认' }}
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.modal-backdrop {
  position: fixed; inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(8px);
  z-index: 9000;
  display: flex; align-items: center; justify-content: center;
  will-change: opacity;
}

.modal-card {
  width: 90%; max-width: 420px;
  background: var(--bg-panel);
  border: 1px solid var(--border-dim);
  border-radius: 24px;
  box-shadow: var(--shadow-float);
  display: flex; flex-direction: column;
  overflow: hidden;
  position: relative;
  will-change: transform, opacity;
  animation: modalIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.modal-header {
  padding: 32px 32px 16px 32px;
}

.modal-title {
  font-size: 20px; font-weight: 700; color: var(--txt-primary);
  letter-spacing: -0.02em;
}

.modal-body {
  padding: 0 32px 32px 32px;
}

.modal-text {
  font-size: 15px; color: var(--txt-secondary);
  line-height: 1.6;
  white-space: pre-wrap;
}

.modal-footer {
  padding: 20px 32px 32px 32px;
  display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
  background: var(--bg-app);
  border-top: 1px solid var(--border-dim);
}

.bento-btn {
  height: 48px;
  border-radius: 14px;
  font-size: 14px; font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  display: flex; align-items: center; justify-content: center;
}
.bento-btn:active { transform: scale(0.98); }

.bento-btn.primary {
  background: var(--brand); color: #fff;
  box-shadow: 0 4px 12px rgba(var(--brand-rgb), 0.25);
}
.bento-btn.primary:hover {
  background: var(--brand-hover);
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(var(--brand-rgb), 0.35);
}

.bento-btn.danger {
  background: var(--error); color: #fff;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.25);
}
.bento-btn.danger:hover { 
  background: #dc2626; 
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(239, 68, 68, 0.35);
}

.bento-btn.ghost {
  background: transparent; color: var(--txt-secondary);
}
.bento-btn.ghost:hover {
  background: var(--bg-hover); color: var(--txt-primary);
}

/* Animation */
.modal-pop-enter-active, .modal-pop-leave-active {
  transition: opacity 0.2s ease;
}
.modal-pop-enter-from, .modal-pop-leave-to {
  opacity: 0;
}

@keyframes modalIn {
  from { opacity: 0; transform: scale(0.95) translateY(10px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
</style>
