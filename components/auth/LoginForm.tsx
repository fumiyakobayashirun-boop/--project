"use client";

// F2: ログインフォーム。送信中の表示とエラー表示のためにクライアントコンポーネントにしている。

import { useActionState } from "react";
import { login, type LoginState } from "@/app/login/actions";

const initialState: LoginState = { error: null, email: "" };

export function LoginForm({ next }: { next: string }) {
  const [state, formAction, pending] = useActionState(login, initialState);

  return (
    <form action={formAction} className="flex flex-col gap-4">
      <input type="hidden" name="next" value={next} />

      <label className="flex flex-col gap-1 text-sm font-medium">
        メールアドレス
        <input
          type="email"
          name="email"
          required
          autoComplete="email"
          defaultValue={state.email}
          className="rounded-md border border-zinc-300 px-3 py-2 text-base font-normal focus:border-emerald-600 focus:outline-none"
        />
      </label>

      <label className="flex flex-col gap-1 text-sm font-medium">
        パスワード
        <input
          type="password"
          name="password"
          required
          autoComplete="current-password"
          className="rounded-md border border-zinc-300 px-3 py-2 text-base font-normal focus:border-emerald-600 focus:outline-none"
        />
      </label>

      {state.error && (
        <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {state.error}
        </p>
      )}

      <button
        type="submit"
        disabled={pending}
        className="rounded-md bg-emerald-700 px-4 py-2 font-semibold text-white hover:bg-emerald-800 disabled:opacity-60"
      >
        {pending ? "ログイン中…" : "ログイン"}
      </button>
    </form>
  );
}
