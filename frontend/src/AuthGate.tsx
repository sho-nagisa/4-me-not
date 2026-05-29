import { useEffect, useState } from "react";
import type { FormEvent, ReactNode } from "react";

import {
  ApiError,
  getCurrentAccount,
  loginAccount,
  logoutAccount,
  registerAccount,
} from "./pages/interactionNew/interactionsApi";
import type { AuthAccount } from "./pages/interactionNew/types";

type AuthMode = "login" | "register";

export function AuthGate({
  children,
}: {
  children: (props: { account: AuthAccount; onLogout: () => Promise<void> }) => ReactNode;
}) {
  const [account, setAccount] = useState<AuthAccount | null>(null);
  const [mode, setMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const loadAccount = async () => {
      try {
        const currentAccount = await getCurrentAccount();
        if (!cancelled) {
          setAccount(currentAccount);
        }
      } catch (error) {
        if (!cancelled && !(error instanceof ApiError && error.status === 401)) {
          setMessage(
            error instanceof Error
              ? error.message
              : "ログイン状態を確認できませんでした。"
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void loadAccount();

    return () => {
      cancelled = true;
    };
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setMessage(null);

    if (!email.trim() || !password) {
      setMessage("メールアドレスとパスワードを入力してください。");
      return;
    }

    setSubmitting(true);
    try {
      const nextAccount =
        mode === "login"
          ? await loginAccount(email.trim(), password)
          : await registerAccount(email.trim(), password);
      setAccount(nextAccount);
      setPassword("");
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : mode === "login"
            ? "ログインに失敗しました。"
            : "登録に失敗しました。"
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logoutAccount();
    } finally {
      setAccount(null);
      setPassword("");
    }
  };

  if (loading) {
    return (
      <main className="auth-shell">
        <section className="auth-panel page-card">
          <p className="auth-status">読み込み中...</p>
        </section>
      </main>
    );
  }

  if (account) {
    return <>{children({ account, onLogout: handleLogout })}</>;
  }

  return (
    <main className="auth-shell">
      <section className="auth-panel page-card">
        <div className="auth-panel__header">
          <div>
            <p className="eyebrow">4-me-not</p>
            <h1>4-me-not</h1>
          </div>
          <div className="section-tabs auth-tabs">
            <button
              type="button"
              className={`section-tab ${mode === "login" ? "section-tab--active" : ""}`}
              onClick={() => {
                setMode("login");
                setMessage(null);
              }}
            >
              ログイン
            </button>
            <button
              type="button"
              className={`section-tab ${
                mode === "register" ? "section-tab--active" : ""
              }`}
              onClick={() => {
                setMode("register");
                setMessage(null);
              }}
            >
              登録
            </button>
          </div>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="field">
            <span className="field__label">メールアドレス</span>
            <input
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          <label className="field">
            <span className="field__label">パスワード</span>
            <input
              type="password"
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              minLength={8}
              maxLength={128}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>

          {message ? (
            <p className="auth-message" role="alert">
              {message}
            </p>
          ) : null}

          <button type="submit" className="button button--primary" disabled={submitting}>
            {submitting ? "処理中..." : mode === "login" ? "ログイン" : "登録して開始"}
          </button>
        </form>
      </section>
    </main>
  );
}
