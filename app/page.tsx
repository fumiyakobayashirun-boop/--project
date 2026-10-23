// トップページ。地域人材マップ（F4）・一覧（F6）はチケット04・06でここに実装する。

import Link from "next/link";

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col items-start justify-center gap-6 px-4 py-16">
      <h1 className="text-3xl font-bold leading-tight">
        地域で挑戦する人に、
        <br />
        会いに行こう。
      </h1>
      <p className="text-zinc-600">
        アンプレ‼で出会った「地域の担い手」は、実際にこのまちにいます。
        マップから気になる人を見つけて、連絡してみましょう。
      </p>
      <p className="rounded-md border border-dashed border-zinc-300 px-4 py-3 text-sm text-zinc-500">
        地域人材マップは準備中です。
      </p>
      <Link href="/login" className="text-sm text-emerald-800 underline">
        ローカルプレイヤーの方はこちらからログイン
      </Link>
    </main>
  );
}
