// F2: proxy.ts（旧middleware）から呼ぶセッション更新処理。
// アクセストークンの期限切れをここで更新し、Cookieをレスポンスに書き戻す。
// あわせて、未ログイン時に編集系ページへのアクセスをログイン画面へ振り向ける。

import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

// ログイン必須のパス（F14本人編集・F13運営管理画面など編集系機能）
const PROTECTED_PREFIXES = ["/mypage", "/admin"];

export async function updateSession(request: NextRequest) {
  let response = NextResponse.next({ request });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet, headers) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value));
          response = NextResponse.next({ request });
          cookiesToSet.forEach(({ name, value, options }) =>
            response.cookies.set(name, value, options),
          );
          // 認証Cookieを含むレスポンスがCDNにキャッシュされないようにする
          Object.entries(headers).forEach(([key, value]) => response.headers.set(key, value));
        },
      },
    },
  );

  // createServerClientとgetClaims()の間に他の処理を挟まないこと（公式ガイドの注意事項）。
  const { data } = await supabase.auth.getClaims();
  const isLoggedIn = Boolean(data?.claims);

  const { pathname, search } = request.nextUrl;
  const isProtected = PROTECTED_PREFIXES.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
  );

  if (!isLoggedIn && isProtected) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.search = `?next=${encodeURIComponent(pathname + search)}`;
    return NextResponse.redirect(url);
  }

  return response;
}
