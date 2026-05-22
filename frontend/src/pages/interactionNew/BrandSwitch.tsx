import { useEffect, useRef, useState } from "react";
import type { PointerEvent } from "react";

import type { WorkspaceMode } from "./navigation";

const MODE_SWITCH_HOLD_MS = 1500;

export function BrandSwitch({
  workspaceMode,
  onToggle,
}: {
  workspaceMode: WorkspaceMode;
  onToggle: () => void;
}) {
  const [modeSwitchArmed, setModeSwitchArmed] = useState(false);
  const modeSwitchTimerRef = useRef<number | null>(null);

  const clearModeSwitchTimer = () => {
    if (modeSwitchTimerRef.current !== null) {
      window.clearTimeout(modeSwitchTimerRef.current);
      modeSwitchTimerRef.current = null;
    }
  };

  const handleModeSwitchPointerDown = (event: PointerEvent<HTMLButtonElement>) => {
    event.currentTarget.setPointerCapture(event.pointerId);
    clearModeSwitchTimer();
    setModeSwitchArmed(true);
    modeSwitchTimerRef.current = window.setTimeout(() => {
      modeSwitchTimerRef.current = null;
      setModeSwitchArmed(false);
      onToggle();
    }, MODE_SWITCH_HOLD_MS);
  };

  const handleModeSwitchPointerEnd = (event: PointerEvent<HTMLButtonElement>) => {
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
    clearModeSwitchTimer();
    setModeSwitchArmed(false);
  };

  useEffect(() => {
    return () => clearModeSwitchTimer();
  }, []);

  return (
    <button
      type="button"
      className={`brand-switch brand-switch--${workspaceMode} ${
        modeSwitchArmed ? "brand-switch--pressing" : ""
      }`}
      onPointerDown={handleModeSwitchPointerDown}
      onPointerUp={handleModeSwitchPointerEnd}
      onPointerCancel={handleModeSwitchPointerEnd}
      onPointerLeave={() => {
        clearModeSwitchTimer();
        setModeSwitchArmed(false);
      }}
      aria-label="勿忘草。3秒長押しで人間関係管理とタスク管理を切り替えます。"
      title="3秒長押しで切り替え"
    >
      <span className="brand-switch__title">勿忘草</span>
      <span className="brand-switch__mode">
        {workspaceMode === "relations" ? "人間関係管理" : "タスク管理"}
      </span>
    </button>
  );
}
