// F2: 全ページのリクエスト前にSupabaseのセッションを更新する（Next.js 16で middleware → proxy に改称）。

import type { NextRequest } from "next/server";
import { updateSession } from "@/lib/supabase/proxy";

export async function proxy(request: NextRequest) {
  return updateSession(request);
}

export const config = {
  matcher: [
    // 静的ファイル・画像最適化・画像ファイルは対象外にする
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
