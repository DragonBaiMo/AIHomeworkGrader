import { createApp } from "vue";
import App from "./App.vue";
import "./assets/main.css";

const app = createApp(App);

const tooltipMap = new WeakMap<HTMLElement, { tip: HTMLDivElement | null; text: string }>();

app.directive("tooltip", {
  mounted(el, binding) {
    const text = String(binding.value ?? "");
    tooltipMap.set(el, { tip: null, text });

    const onEnter = () => {
      const state = tooltipMap.get(el);
      if (!state || !state.text) return;
      if (state.tip) return;

      const tip = document.createElement("div");
      tip.className = "v-tooltip-pop";
      tip.textContent = state.text;
      document.body.appendChild(tip);
      state.tip = tip;

      const rect = el.getBoundingClientRect();
      const tipRect = tip.getBoundingClientRect();
      const left = rect.left + rect.width / 2 - tipRect.width / 2;
      const top = rect.top - tipRect.height - 10;
      tip.style.left = `${Math.max(8, left)}px`;
      tip.style.top = `${Math.max(8, top)}px`;
    };

    const onLeave = () => {
      const state = tooltipMap.get(el);
      if (!state?.tip) return;
      state.tip.remove();
      state.tip = null;
    };

    (el as any).__vTooltipEnter__ = onEnter;
    (el as any).__vTooltipLeave__ = onLeave;
    el.addEventListener("mouseenter", onEnter, { passive: true });
    el.addEventListener("mouseleave", onLeave, { passive: true });
  },
  updated(el, binding) {
    const state = tooltipMap.get(el);
    if (!state) return;
    state.text = String(binding.value ?? "");
    if (state.tip) {
      state.tip.textContent = state.text;
    }
  },
  unmounted(el) {
    const state = tooltipMap.get(el);
    if (state?.tip) {
      state.tip.remove();
    }
    tooltipMap.delete(el);

    const onEnter = (el as any).__vTooltipEnter__ as undefined | (() => void);
    const onLeave = (el as any).__vTooltipLeave__ as undefined | (() => void);
    if (onEnter) el.removeEventListener("mouseenter", onEnter);
    if (onLeave) el.removeEventListener("mouseleave", onLeave);
    delete (el as any).__vTooltipEnter__;
    delete (el as any).__vTooltipLeave__;
  },
});

app.mount("#app");
