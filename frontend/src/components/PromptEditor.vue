<style scoped>
.editor-shell {
  display: flex; flex-direction: column; height: 100%; background: var(--bg-app);
}

.editor-bar {
  height: 48px; border-bottom: 1px solid var(--border-dim);
  display: flex; justify-content: space-between; align-items: center;
  padding: 0 24px; background: var(--bg-panel);
}
.bar-left { display: flex; align-items: center; gap: 8px; color: var(--brand); }
.bar-title { font-weight: 600; font-size: 14px; color: var(--txt-primary); }
.bar-right { display: flex; gap: 12px; }

/* Icons & Buttons */
.icon-btn {
  background: transparent; border: none; color: var(--txt-tertiary);
  cursor: pointer; padding: 6px; border-radius: 4px;
  display: flex; align-items: center; justify-content: center; transition: all 0.2s;
}
.icon-btn:hover { color: var(--txt-primary); background: var(--bg-active); }
.icon-btn.highlight:hover { color: var(--brand); background: var(--brand-dim); }
.icon-btn.danger:hover { color: var(--error); background: var(--error-bg); }
.icon-btn.big { padding: 8px; }
.btn.icon-only { width: 32px; padding: 0; }
.btn-text { margin-left: 4px; }
.icon-text-desktop { display: inline-flex; }

/* Layout */
.ide-container { display: flex; flex: 1; overflow: hidden; }

.sidebar-pane {
  width: 240px; background: var(--bg-panel);
  border-right: 1px solid var(--border-dim);
  display: flex; flex-direction: column; flex-shrink: 0;
}
@media (max-width: 768px) {
  .ide-container { flex-direction: column; }
  .sidebar-pane { width: 100%; height: auto; max-height: 120px; border-right: none; border-bottom: 1px solid var(--border-dim); }
  .file-list { flex-direction: row; overflow-x: auto; padding-bottom: 8px; }
  .file-item { white-space: nowrap; }
  .editor-bar { padding: 0 16px; }
  .icon-text-desktop { display: none; }
  .btn-text { margin-left: 0; }
}

.pane-header {
  padding: 16px; font-size: 12px; font-weight: 600; color: var(--txt-tertiary);
  display: flex; justify-content: space-between; align-items: center;
}
.file-list { display: flex; flex-direction: column; padding: 0 8px; gap: 2px; }
.file-item {
  display: flex; align-items: center; gap: 8px; padding: 8px 12px;
  background: transparent; border: none; border-radius: 4px; cursor: pointer;
  color: var(--txt-secondary); font-family: "JetBrains Mono", monospace; font-size: 13px; text-align: left;
}
.file-item:hover { background: var(--bg-active); color: var(--txt-primary); }
.file-item.active { background: var(--bg-active); color: var(--brand); }
.file-icon { opacity: 0.5; }

.editor-pane {
  flex: 1; overflow-y: auto; padding: 32px 40px;
  display: flex; flex-direction: column; gap: 32px;
}
@media (max-width: 768px) { .editor-pane { padding: 20px 16px; gap: 24px; } }

/* Config Header */
.config-header-card {
  display: flex; flex-direction: column; gap: 16px;
  padding-bottom: 32px; border-bottom: 1px dashed var(--border-dim);
}
.header-row { display: flex; gap: 16px; align-items: flex-end; }
.grow { flex: 1; }
.field-group label {
  display: block; font-size: 12px; color: var(--txt-tertiary); margin-bottom: 8px; font-weight: 500;
}
.code-input {
  width: 100%; background: var(--bg-card); border: 1px solid var(--border-dim);
  color: var(--txt-primary); padding: 10px; font-family: "JetBrains Mono", monospace;
  font-size: 13px; border-radius: var(--radius-s);
}
.code-input:focus { border-color: var(--brand); outline: none; }
.code-input.area { min-height: 80px; line-height: 1.6; }

/* Rules Stack */
.rules-stack { display: flex; flex-direction: column; gap: 16px; }
.stack-label { font-size: 12px; font-weight: 600; color: var(--txt-tertiary); margin-bottom: 8px; }

/* Module Block */
.module-block {
  border: 1px solid var(--border-dim); border-radius: var(--radius-m);
  background: var(--bg-panel); overflow: hidden;
  transition: all 0.3s var(--ease-out);
}
.module-block.collapsed { border-color: transparent; background: var(--bg-panel); }

.module-head {
  display: flex; justify-content: space-between; padding: 10px 16px;
  background: var(--bg-panel); border-bottom: 1px solid var(--border-dim);
  align-items: center; cursor: pointer; user-select: none; transition: background 0.2s;
}
.module-head:hover { background: var(--bg-active); }
.module-block.collapsed .module-head { border-bottom-color: transparent; }

.head-left, .head-right { display: flex; align-items: center; gap: 12px; }
.chevron-box {
  color: var(--txt-tertiary); display: flex; align-items: center;
  transition: transform 0.3s var(--ease-spring);
}
.chevron-box.rotate { transform: rotate(90deg); }

.transparent-input {
  background: transparent; border: none; color: var(--txt-primary);
  font-family: inherit; font-size: 14px;
}
.transparent-input.title { font-weight: 600; width: 220px; cursor: text; }
.transparent-input.num { width: 40px; text-align: center; color: var(--brand); cursor: text; font-family: "JetBrains Mono"; }
.tag { font-size: 12px; color: var(--txt-tertiary); }
.divider { width: 1px; height: 16px; background: var(--border-dim); margin: 0 4px; }

@media (max-width: 600px) {
  .transparent-input.title { width: 140px; text-overflow: ellipsis; }
  .mobile-hide { display: none; }
  .head-left, .head-right { gap: 8px; }
  .module-head { padding: 10px 12px; }
}

/* --- New Item Card Style --- */
.items-wrapper {
  background: var(--bg-card); padding: 16px;
}
.items-grid {
  display: flex; flex-direction: column; gap: 8px;
}

.item-card {
  background: var(--bg-panel); border: 1px solid var(--border-dim);
  border-radius: var(--radius-s); overflow: hidden;
  transition: border-color 0.2s;
}
.item-card:hover { border-color: var(--border-light); }

/* Item Header */
.item-head {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 12px; cursor: pointer; user-select: none;
  background: var(--bg-panel);
}
.item-head-left, .item-head-right { display: flex; align-items: center; gap: 10px; }

.tiny-chevron {
  width: 16px; height: 16px; display: flex; align-items: center; justify-content: center;
  color: var(--txt-tertiary); transition: transform 0.2s;
}
.tiny-chevron.open { transform: rotate(90deg); color: var(--txt-primary); }

.item-key-input {
  background: transparent; border: none; color: var(--error);
  font-family: "JetBrains Mono"; font-size: 13px; font-weight: 500;
  width: 180px;
}
.item-key-input:focus { outline: none; background: var(--bg-active); border-radius: 4px; }

.item-score-input {
  width: 36px; background: transparent; border: 1px solid var(--border-dim);
  border-radius: 4px; text-align: center; color: var(--brand);
  font-family: "JetBrains Mono"; font-size: 13px; padding: 2px 0;
}
.item-score-input:focus { border-color: var(--brand); outline: none; background: var(--bg-active); }
.item-tag { font-size: 11px; color: var(--txt-tertiary); }

/* Item Body */
.item-body {
  border-top: 1px solid var(--border-dim);
  padding: 0; background: var(--bg-hover);
}
.desc-textarea {
  width: 100%; border: none; background: transparent; padding: 12px;
  color: var(--success); font-family: "JetBrains Mono"; font-size: 13px;
  resize: vertical; min-height: 60px; line-height: 1.5; display: block;
}
.desc-textarea:focus { outline: none; background: var(--bg-active); }

/* Mobile Adjustments for Item Card */
@media (max-width: 600px) {
  .item-head { padding: 10px; }
  .item-key-input { width: 120px; }
  .item-tag { display: none; }
}

.add-item-btn {
  margin-top: 8px; align-self: flex-start;
  background: transparent; border: 1px dashed var(--border-dim);
  color: var(--txt-tertiary); padding: 8px 16px; border-radius: var(--radius-s);
  cursor: pointer; display: flex; align-items: center; gap: 6px; font-size: 12px;
}
.add-item-btn:hover { color: var(--txt-primary); border-color: var(--txt-secondary); background: var(--bg-panel); }

.new-module-btn {
  width: 100%; padding: 12px; border: 1px dashed var(--border-dim);
  background: transparent; color: var(--txt-tertiary); cursor: pointer;
  border-radius: var(--radius-m); display: flex; align-items: center; justify-content: center;
  gap: 8px; font-size: 13px;
}
.new-module-btn:hover { border-color: var(--txt-secondary); color: var(--txt-primary); background: var(--bg-active); }

/* Transitions */
.list-anim-move, .list-anim-enter-active, .list-anim-leave-active { transition: all 0.3s var(--ease-spring); }
.list-anim-enter-from, .list-anim-leave-to { opacity: 0; transform: scale(0.98); }
</style>