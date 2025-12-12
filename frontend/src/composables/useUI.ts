import { reactive, ref } from "vue";

export type ToastType = "success" | "error" | "info" | "warning";

export interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

export interface ModalOptions {
  title: string;
  content: string;
  confirmText?: string;
  cancelText?: string;
  type?: "danger" | "normal";
  onConfirm: () => void;
  onCancel?: () => void;
}

// State
const toasts = reactive<Toast[]>([]);
const modalState = reactive<{
  isOpen: boolean;
  options: ModalOptions | null;
}>({
  isOpen: false,
  options: null,
});

// Logic
export function useUI() {
  // --- Toast ---
  function showToast(message: string, type: ToastType = "info") {
    const id = Date.now().toString() + Math.random();
    toasts.push({ id, message, type });
    setTimeout(() => {
      removeToast(id);
    }, 3000);
  }

  function removeToast(id: string) {
    const idx = toasts.findIndex((t) => t.id === id);
    if (idx !== -1) toasts.splice(idx, 1);
  }

  // --- Modal ---
  function confirm(options: ModalOptions) {
    modalState.options = options;
    modalState.isOpen = true;
  }

  function closeModal() {
    modalState.isOpen = false;
    setTimeout(() => {
      modalState.options = null;
    }, 300); // Wait for anim
  }

  return {
    toasts,
    modalState,
    showToast,
    removeToast,
    confirm,
    closeModal,
  };
}
