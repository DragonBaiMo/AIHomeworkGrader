<script setup lang="ts">
import { useUI } from "@/composables/useUI";

const { modalState, closeModal } = useUI();

function handleConfirm() {
  if (modalState.onConfirm) modalState.onConfirm();
  closeModal();
}
</script>

<template>
  <Transition name="modal-fade">
    <div v-if="modalState.show" class="modal-backdrop" @click.self="closeModal">
      <div class="modal-card">
        <h3 class="modal-title">{{ modalState.title }}</h3>
        <p class="modal-content">{{ modalState.content }}</p>
        
        <div class="modal-actions">
          <button class="btn ghost" @click="closeModal">取消</button>
          <button 
            class="btn" 
            :class="modalState.type === 'danger' ? 'danger' : 'primary'"
            @click="handleConfirm"
          >
            {{ modalState.confirmText || '确认' }}
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
  backdrop-filter: blur(4px);
  z-index: 9000;
  display: flex; align-items: center; justify-content: center;
}

.modal-card {
  width: 90%; max-width: 400px;
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-l);
  padding: 32px;
  box-shadow: var(--shadow-float);
  display: flex; flex-direction: column; gap: 20px;
  text-align: center;
}

.modal-title { font-size: 20px; font-weight: 700; color: var(--txt-primary); }
.modal-content { font-size: 14px; color: var(--txt-secondary); line-height: 1.6; }

.modal-actions { display: flex; gap: 12px; justify-content: center; margin-top: 8px; }
.modal-actions .btn { min-width: 100px; }

.modal-fade-enter-active, .modal-fade-leave-active { transition: opacity 0.3s; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }
.modal-fade-enter-active .modal-card { animation: popIn 0.3s var(--ease-spring); }
.modal-fade-leave-active .modal-card { animation: popIn 0.3s var(--ease-spring) reverse; }

@keyframes popIn {
  from { transform: scale(0.9); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
</style>
