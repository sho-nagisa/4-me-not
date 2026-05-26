import type { ReactNode } from "react";

import { mobilePageOptions, pageOptions } from "./constants";
import { BrandSwitch } from "./BrandSwitch";
import { NavItem } from "./components";
import { taskPageOptions, type WorkspaceMode } from "./navigation";
import type { PageId } from "./types";
import type { TaskPanelId } from "./TaskPage";

export type FeedbackState = {
  tone: "success" | "error" | "info";
  message: string;
} | null;

export function InteractionNewLayout({
  isMobile,
  workspaceMode,
  currentPage,
  setCurrentPage,
  taskPanel,
  setTaskPanel,
  relationSummary,
  taskSummary,
  feedback,
  accountEmail,
  isOnline,
  pendingInteractionCount,
  isSyncingInteractions,
  onDismissFeedback,
  onLogout,
  onToggleWorkspaceMode,
  children,
}: {
  isMobile: boolean;
  workspaceMode: WorkspaceMode;
  currentPage: PageId;
  setCurrentPage: (page: PageId) => void;
  taskPanel: TaskPanelId;
  setTaskPanel: (panel: TaskPanelId) => void;
  relationSummary: {
    totalCount: number;
    personCount: number;
    communityCount: number;
  };
  taskSummary: {
    candidateCount: number;
    openCount: number;
    dueSoonCount: number;
  };
  feedback: FeedbackState;
  accountEmail: string;
  isOnline: boolean;
  pendingInteractionCount: number;
  isSyncingInteractions: boolean;
  onDismissFeedback: () => void;
  onLogout: () => Promise<void>;
  onToggleWorkspaceMode: () => void;
  children: ReactNode;
}) {
  const brandSwitch = (
    <BrandSwitch workspaceMode={workspaceMode} onToggle={onToggleWorkspaceMode} />
  );
  const accountPanel = (
    <div className="account-panel">
      <div className="account-panel__identity">
        <span>ログイン中</span>
        <strong title={accountEmail}>{accountEmail}</strong>
      </div>
      <button
        type="button"
        className="button button--ghost button--small"
        onClick={() => void onLogout()}
      >
        ログアウト
      </button>
    </div>
  );
  const feedbackBanner = feedback ? (
    <section className={`banner banner--${feedback.tone}`}>
      <p>{feedback.message}</p>
      <button
        type="button"
        className="banner__close"
        onClick={onDismissFeedback}
        aria-label="通知を閉じる"
      >
        ×
      </button>
    </section>
  ) : null;
  const offlineBanner = !isOnline ? (
    <section className="offline-banner" role="status" aria-live="polite">
      <strong>オフラインです</strong>
      <span>
        表示中の内容は古い可能性があります。保存した記録は未送信として残します。
        {pendingInteractionCount > 0 ? ` 未送信 ${pendingInteractionCount}件。` : ""}
      </span>
    </section>
  ) : isSyncingInteractions ? (
    <section className="offline-banner offline-banner--syncing" role="status" aria-live="polite">
      <strong>送信中です</strong>
      <span>未送信の記録を同期しています。</span>
    </section>
  ) : null;

  return (
    <main
      className={`app-shell ${isMobile ? "app-shell--mobile" : "app-shell--desktop"} ${
        workspaceMode === "relations" && currentPage === "home" ? "app-shell--home" : ""
      } app-shell--${workspaceMode}`}
    >
      <div className="app-shell__glow app-shell__glow--left" />
      <div className="app-shell__glow app-shell__glow--right" />

      {!isMobile ? (
        <div className="desktop-frame">
          <aside className="desktop-sidebar">
            <div className="brand-card brand-card--compact">{brandSwitch}</div>
            {accountPanel}

            <nav className="nav-list">
              {workspaceMode === "relations"
                ? pageOptions.map((page) => (
                    <NavItem
                      key={page.id}
                      active={currentPage === page.id}
                      label={page.label}
                      description={page.description}
                      onClick={() => setCurrentPage(page.id)}
                    />
                  ))
                : taskPageOptions.map((page) => (
                    <NavItem
                      key={page.id}
                      active={taskPanel === page.id}
                      label={page.label}
                      description={page.description}
                      onClick={() => setTaskPanel(page.id)}
                    />
                  ))}
            </nav>

            <div className="sidebar-summary">
              {workspaceMode === "relations" ? (
                <>
                  <div className="sidebar-summary__item">
                    <strong>{relationSummary.totalCount}</strong>
                    <span>記録数</span>
                  </div>
                  <div className="sidebar-summary__item">
                    <strong>{relationSummary.personCount}</strong>
                    <span>人</span>
                  </div>
                  <div className="sidebar-summary__item">
                    <strong>{relationSummary.communityCount}</strong>
                    <span>コミュニティ</span>
                  </div>
                </>
              ) : (
                <>
                  <div className="sidebar-summary__item">
                    <strong>{taskSummary.candidateCount}</strong>
                    <span>候補</span>
                  </div>
                  <div className="sidebar-summary__item">
                    <strong>{taskSummary.openCount}</strong>
                    <span>未完了</span>
                  </div>
                  <div className="sidebar-summary__item">
                    <strong>{taskSummary.dueSoonCount}</strong>
                    <span>期限間近</span>
                  </div>
                </>
              )}
            </div>
          </aside>

          <section className="desktop-content">
            {offlineBanner}
            {feedbackBanner}
            {children}
          </section>
        </div>
      ) : (
        <div className="mobile-frame">
          <header className="mobile-header mobile-header--compact mobile-header--account">
            {brandSwitch}
            {accountPanel}
          </header>

          {offlineBanner}
          {feedbackBanner}

          <section className="mobile-content">{children}</section>

          <nav className="mobile-dock">
            {workspaceMode === "relations"
              ? mobilePageOptions.map((page) => (
                  <NavItem
                    key={page.id}
                    active={currentPage === page.id}
                    compact
                    label={page.mobileLabel}
                    description=""
                    onClick={() => setCurrentPage(page.id)}
                  />
                ))
              : taskPageOptions.map((page) => (
                  <NavItem
                    key={page.id}
                    active={taskPanel === page.id}
                    compact
                    label={page.mobileLabel}
                    description=""
                    onClick={() => setTaskPanel(page.id)}
                  />
                ))}
          </nav>
        </div>
      )}
    </main>
  );
}
