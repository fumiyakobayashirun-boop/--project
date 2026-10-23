// マイページ（ログイン必須）。
// 現時点ではF2の動作確認用。本人編集フォームはF14（チケット14）でここに実装する。

import type { Metadata } from "next";
import { requireUser } from "@/lib/auth";

export const metadata: Metadata = { title: "マイページ" };

const MEMBER_TYPE_LABEL = { local_player: "ローカルプレイヤー", user: "利用者" } as const;

export default async function MyPage() {
  // proxy.tsでも保護しているが、ページ側でも必ず確認する（多重の防御）
  const { email, profile } = await requireUser("/mypage");

  return (
    <main className="mx-auto w-full max-w-2xl flex-1 px-4 py-12">
      <h1 className="mb-6 text-2xl font-bold">マイページ</h1>
      <dl className="grid grid-cols-[8rem_1fr] gap-y-3 rounded-lg border border-zinc-200 bg-white p-6 text-sm">
        <dt className="text-zinc-500">メールアドレス</dt>
        <dd>{email}</dd>
        <dt className="text-zinc-500">表示名</dt>
        <dd>{profile?.displayName ?? "（未登録）"}</dd>
        <dt className="text-zinc-500">会員種別</dt>
        <dd>{profile ? MEMBER_TYPE_LABEL[profile.memberType] : "（未登録）"}</dd>
      </dl>
      {!profile && (
        <p className="mt-4 text-sm text-zinc-600">
          プロフィールはまだ登録されていません（会員登録はF3で実装予定）。
        </p>
      )}
    </main>
  );
}
