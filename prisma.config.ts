// Prisma CLI（migrate/studio/db seed等）の設定。
// Prisma 7以降、接続URLはschema.prismaではなくここで指定する。
// CLIコマンド（マイグレーション等）はSupabaseの直接接続(DIRECT_URL)を使う
// （pgbouncer経由のプール接続はマイグレーションに向かないため）。
// Next.jsの慣習に合わせ.env.localに環境変数を置いているため、明示的に読み込む
// （dotenv/configの既定は.envのみを見るため、.env.localは自動では読まれない）。
import { config } from "dotenv";
import { defineConfig, env } from "prisma/config";

config({ path: ".env.local" });

export default defineConfig({
  schema: "prisma/schema.prisma",
  migrations: {
    path: "prisma/migrations",
    seed: "tsx prisma/seed.ts",
  },
  datasource: {
    url: env("DIRECT_URL"),
  },
});
