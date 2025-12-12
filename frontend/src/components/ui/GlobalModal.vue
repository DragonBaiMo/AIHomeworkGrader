<script setup lang="ts">
import { useUI } from "@/composables/useUI";

const { modalState, closeModal } = useUI();

function handleConfirm() {
  modalState.options?.onConfirm();
  closeModal();
}

function handleCancel() {
  modalState.options?.onCancel?.();
  closeModal();
}
</script>

<template>
  <Transition name="modal-fade">
    <div v-if="modalState.isOpen" class="modal-backdrop" @click.self="handleCancel">
      <div class="modal-card">
        <h3 class="modal-title">{{ modalState.options?.title }}</h3>
        <p class="modal-content">{{ modalState.options?.content }}</p>
        
        <div class="modal-actions">
          <button class="btn ghost" @click="handleCancel">
            {{ modalState.options?.cancelText || "取消" }}
          </button>
          <button 
            class="btn" 
            :class="modalState.options?.type === 'danger' ? 'danger' : 'primary'"
            @click="handleConfirm"
          >
            {{ modalState.options?.confirmText || "确认" }}
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  z-index: 9998;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.modal-card {
  background: var(--bg-panel);
  border: 1px solid var(--border-dim);
  border-radius: 20px;
  padding: 32px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 20px 50px -10px rgba(0,0,0,0.3);
  display: flex;
  flex-direction: column;
  gap: 16px;
  transform-origin: center;
}

.modal-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--txt-primary);
}

.modal-content {
  font-size: 15px;
  color: var(--txt-secondary);
  line-height: 1.6;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
}

/* Transitions */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.3s ease;
}
.modal-fade-enter-active .modal-card,
.modal-fade-leave-active .modal-card {
  transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
.modal-fade-enter-from .modal-card {
  transform: scale(0.9) translateY(20px);
}
.modal-fade-leave-to .modal-card {
  transform: scale(0.95) translateY(10px);
}
</style>