/**
 * Phase 8 — TaskProgressPanel
 * Shows real-time agentic task step progress.
 * Appears only when a multi-step task is actively running.
 */

import { useJarvisStore, type TaskStep, type TaskStepStatus } from '../stores/jarvisStore';
import { motion, AnimatePresence } from 'framer-motion';

// ── Status icon per step ──────────────────────────────────────────────────────

function StepIcon({ status }: { status: TaskStepStatus }) {
  if (status === 'done') {
    return (
      <svg className="task-step-icon task-step-icon--done" viewBox="0 0 16 16" fill="none">
        <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5" />
        <path d="M5 8l2 2 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  }
  if (status === 'failed') {
    return (
      <svg className="task-step-icon task-step-icon--failed" viewBox="0 0 16 16" fill="none">
        <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5" />
        <path d="M5.5 5.5l5 5M10.5 5.5l-5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    );
  }
  if (status === 'running') {
    return (
      <motion.svg
        className="task-step-icon task-step-icon--running"
        viewBox="0 0 16 16"
        fill="none"
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
      >
        <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.5" strokeDasharray="28" strokeDashoffset="10" />
      </motion.svg>
    );
  }
  if (status === 'awaiting_confirmation') {
    return (
      <motion.div
        className="task-step-icon task-step-icon--confirm"
        animate={{ scale: [1, 1.2, 1] }}
        transition={{ repeat: Infinity, duration: 1.2 }}
      >
        ⚠
      </motion.div>
    );
  }
  // pending
  return <div className="task-step-icon task-step-icon--pending">○</div>;
}

// ── Single step row ───────────────────────────────────────────────────────────

function TaskStepRow({ step, isCurrent }: { step: TaskStep; isCurrent: boolean }) {
  return (
    <motion.div
      className={`task-step-row ${isCurrent ? 'task-step-row--active' : ''} task-step-row--${step.status}`}
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.25 }}
    >
      <StepIcon status={step.status} />
      <span className="task-step-desc">{step.description}</span>
    </motion.div>
  );
}

// ── Main panel ────────────────────────────────────────────────────────────────

export function TaskProgressPanel() {
  const activeTask = useJarvisStore((s) => s.activeTask);

  return (
    <AnimatePresence>
      {activeTask && (
        <motion.div
          className="task-progress-panel glass-panel"
          initial={{ opacity: 0, y: 16, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 16, scale: 0.97 }}
          transition={{ duration: 0.3 }}
        >
          {/* Header */}
          <div className="task-progress-header">
            <div className="task-progress-title">
              {activeTask.done ? '✅ Task Complete' : '⚡ Task in Progress'}
            </div>
            <div className="task-progress-counter">
              {activeTask.done
                ? `${activeTask.completed}/${activeTask.total} steps`
                : `${activeTask.current}/${activeTask.total}`}
            </div>
          </div>

          {/* Progress bar */}
          <div className="task-progress-bar-track">
            <motion.div
              className="task-progress-bar-fill"
              initial={{ width: '0%' }}
              animate={{
                width: `${((activeTask.done ? activeTask.total : activeTask.current - 1) / activeTask.total) * 100}%`,
              }}
              transition={{ duration: 0.4 }}
            />
          </div>

          {/* Steps */}
          <div className="task-steps-list">
            {activeTask.steps.map((step) => (
              <TaskStepRow
                key={step.id}
                step={step}
                isCurrent={!activeTask.done && step.id === activeTask.current}
              />
            ))}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
