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
      <div class="modal-card glass-morphism">
        <div class="modal-body">
          <h3 class="modal-title">{{ modalState.options.title }}</h3>
          <p class="modal-text">{{ modalState.options.content }}</p>
        </div>
        
        <div class="modal-footer">
          <button class="action-btn ghost" @click="closeModal">
            {{ modalState.options.cancelText || '取消' }}
          </button>
          <button 
            class="action-btn" 
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
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(12px);
  z-index: 9000;
  display: flex; align-items: center; justify-content: center;
}

.modal-card {
  width: 90%; max-width: 400px;
  background: var(--bg-panel);
  border: 1px solid var(--border-light);
  border-radius: 20px;
  box-shadow: var(--shadow-float);
  display: flex; flex-direction: column;
  overflow: hidden;
  position: relative;
}
/* Highlight */
.modal-card::before {
  content: ""; position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
}

.modal-body {
  padding: 32px 32px 24px 32px;
  display: flex; flex-direction: column; gap: 12px;
  text-align: center;
}

.modal-title {
  font-size: 18px; font-weight: 700; color: var(--txt-primary);
  letter-spacing: -0.02em;
}

.modal-text {
  font-size: 14px; color: var(--txt-secondary);
  line-height: 1.6;
  white-space: pre-wrap;
}

.modal-footer {
  padding: 20px 24px 24px 24px;
  display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
  background: var(--bg-app);
  border-top: 1px solid var(--border-dim);
}

.action-btn {
  height: 40px;
  border-radius: 10px;
  font-size: 13px; font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
  display: flex; align-items: center; justify-content: center;
}
.action-btn:active { transform: scale(0.98); }

.action-btn.primary {
  background: var(--brand); color: #fff;
  box-shadow: 0 4px 12px rgba(var(--brand-rgb), 0.2);
}
.action-btn.primary:hover {
  background: var(--brand-hover);
  box-shadow: 0 6px 16px rgba(var(--brand-rgb), 0.3);
}

.action-btn.danger {
  background: var(--error); color: #fff;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
}
.action-btn.danger:hover { background: #dc2626; }

.action-btn.ghost {
  background: transparent; color: var(--txt-secondary);
}
.action-btn.ghost:hover {
  background: var(--bg-hover); color: var(--txt-primary);
}

/* Animation */
.modal-pop-enter-active, .modal-pop-leave-active {
  transition: all 0.3s cubic-bezier(0.19, 1, 0.22, 1);
}
.modal-pop-enter-from, .modal-pop-leave-to {
  opacity: 0;
}
.modal-pop-enter-active .modal-card {
  transition: all 0.3s cubic-bezier(0.19, 1, 0.22, 1);
}
.modal-pop-leave-active .modal-card {
  transition: all 0.2s ease-in;
}
.modal-pop-enter-from .modal-card,
.modal-pop-leave-to .modal-card {
  opacity: 0;
  transform: scale(0.9) translateY(10px);
}
</style>
