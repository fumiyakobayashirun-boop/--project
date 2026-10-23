// F2: サーバーコンポーネント・Server Action・Route Handler用のSupabaseクライアント。
// リクエストごとに新しいクライアントを作る（公式ガイド: https://supabase.com/docs/guides/auth/server-side/nextjs）。

import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";

export async function createClient() {
  const cookieStore = await cookies();

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options),
            );
          } catch {
            // サーバーコンポーネントからはCookieを書き込めない。
            // セッションの更新はproxy.tsが担うため、ここでは無視してよい。
          }
        },
      },
    },
  );
}
