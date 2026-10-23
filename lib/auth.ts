// F2: ログイン中のユーザー情報を取得するサーバー専用ヘルパー。
//
// デモ用の簡易実装。本番化前に要強化（詳細設計仕様書 F2・8章）：
// メール確認・パスワードリセット・二段階認証・権限の厳格化は意図的に実装していない。

import "server-only";

import { redirect } from "next/navigation";
import { cache } from "react";
import { prisma } from "@/lib/prisma";
import { createClient } from "@/lib/supabase/server";

export type CurrentUser = {
  authUserId: string;
  email: string;
  /** usersテーブルのプロフィール。F3の会員登録前はnull */
  profile: Awaited<ReturnType<typeof findProfile>>;
};

function findProfile(authUserId: string) {
  return prisma.user.findUnique({
    where: { authUserId },
    select: { id: true, memberType: true, displayName: true },
  });
}

/** ログイン中ならユーザー情報を、未ログインならnullを返す（1リクエスト内ではキャッシュされる） */
export const getCurrentUser = cache(async (): Promise<CurrentUser | null> => {
  const supabase = await createClient();
  // getClaims()はJWTの署名を検証するため、Cookieの中身をそのまま信用するgetSession()より安全
  const { data } = await supabase.auth.getClaims();
  const claims = data?.claims;
  if (!claims?.sub) return null;

  return {
    authUserId: claims.sub,
    email: typeof claims.email === "string" ? claims.email : "",
    profile: await findProfile(claims.sub),
  };
});

/** ログイン必須のページ・Server Actionで使う。未ログインならログイン画面へ移動する */
export async function requireUser(nextPath: string): Promise<CurrentUser> {
  const user = await getCurrentUser();
  if (!user) redirect(`/login?next=${encodeURIComponent(nextPath)}`);
  return user;
}

/** ログイン後の遷移先として安全なパスだけを通す（外部サイトへのオープンリダイレクト対策） */
export function safeNextPath(next: unknown, fallback = "/mypage"): string {
  if (typeof next !== "string" || !next.startsWith("/") || next.startsWith("//") || next.startsWith("/\\")) {
    return fallback;
  }
  return next;
}
