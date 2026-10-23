"use server";

// F2: ログイン・ログアウトのServer Action。
// デモ用の簡易実装。本番化前に要強化（ログイン試行回数の制限などは未実装）。

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { safeNextPath } from "@/lib/auth";
import { createClient } from "@/lib/supabase/server";

export type LoginState = { error: string | null; email: string };

export async function login(_prev: LoginState, formData: FormData): Promise<LoginState> {
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  if (!email || !password) {
    return { error: "メールアドレスとパスワードを入力してください。", email };
  }

  const supabase = await createClient();
  const { error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) {
    return { error: toJapaneseMessage(error.code), email };
  }

  revalidatePath("/", "layout");
  redirect(safeNextPath(formData.get("next")));
}

export async function logout() {
  const supabase = await createClient();
  await supabase.auth.signOut();
  revalidatePath("/", "layout");
  redirect("/");
}

function toJapaneseMessage(code: string | undefined): string {
  switch (code) {
    case "invalid_credentials":
      return "メールアドレスまたはパスワードが正しくありません。";
    case "email_not_confirmed":
      // デモではメール確認を使わない方針（Supabaseの「Confirm email」をOFFにする）
      return "メールアドレスの確認が完了していません。運営にお問い合わせください。";
    case "over_request_rate_limit":
      return "短時間に試行が集中しています。しばらく待ってからお試しください。";
    default:
      return "ログインできませんでした。時間をおいて再度お試しください。";
  }
}
