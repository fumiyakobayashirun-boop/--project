// 全ページ共通のヘッダー。ログイン状態に応じてリンクを出し分ける（F2）。

import Link from "next/link";
import { logout } from "@/app/login/actions";
import { getCurrentUser } from "@/lib/auth";

export async function SiteHeader() {
  const user = await getCurrentUser();

  return (
    <header className="border-b border-zinc-200 bg-white">
      <div className="mx-auto flex h-14 w-full max-w-5xl items-center justify-between gap-3 px-4">
        <Link href="/" className="text-sm font-bold leading-tight text-emerald-800 sm:text-base">
          アンプレ‼ ローカルプレイヤーマップ
        </Link>
        <nav className="flex shrink-0 items-center gap-4 whitespace-nowrap text-sm">
          {user ? (
            <>
              <Link href="/mypage" className="hover:underline">
                マイページ
              </Link>
              <form action={logout}>
                <button type="submit" className="text-zinc-600 hover:underline">
                  ログアウト
                </button>
              </form>
            </>
          ) : (
            <Link
              href="/login"
              className="rounded-md bg-emerald-700 px-3 py-1.5 font-semibold text-white hover:bg-emerald-800"
            >
              ログイン
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
