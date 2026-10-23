// F2: ログイン画面。

import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { LoginForm } from "@/components/auth/LoginForm";
import { getCurrentUser, safeNextPath } from "@/lib/auth";

export const metadata: Metadata = { title: "ログイン" };

export default async function LoginPage({ searchParams }: PageProps<"/login">) {
  const { next } = await searchParams;
  const nextPath = safeNextPath(next);

  // ログイン済みならそのまま目的のページへ
  if (await getCurrentUser()) redirect(nextPath);

  return (
    <main className="mx-auto w-full max-w-sm flex-1 px-4 py-12">
      <h1 className="mb-2 text-2xl font-bold">ログイン</h1>
      <p className="mb-8 text-sm text-zinc-600">
        登録済みのメールアドレスとパスワードでログインしてください。
      </p>
      <LoginForm next={nextPath} />
      <p className="mt-6 text-xs text-zinc-500">
        パスワードを忘れた場合は、運営（パストーン）までお問い合わせください。
      </p>
    </main>
  );
}
