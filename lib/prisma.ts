// Prismaクライアントのシングルトン初期化。
// Next.jsの開発時ホットリロードで接続が増殖しないよう、globalThisにキャッシュする
// （公式ドキュメント推奨パターン: https://www.prisma.io/docs/orm/more/help-and-troubleshooting/help-articles/nextjs-prisma-client-dev-practices）。
//
// Prisma 7ではランタイムの接続にドライバアダプタが必須。
// アプリからの通常アクセスはSupabaseのpgbouncer経由プール接続(DATABASE_URL)を使う
// （マイグレーション専用の直接接続DIRECT_URLはprisma.config.ts側で使用）。

import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "@prisma/client";

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
};

const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL });

export const prisma = globalForPrisma.prisma ?? new PrismaClient({ adapter });

if (process.env.NODE_ENV !== "production") {
  globalForPrisma.prisma = prisma;
}
