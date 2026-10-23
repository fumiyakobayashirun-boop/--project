-- F2: パスワード管理をSupabase Auth（auth.users）へ移し、usersテーブルとの紐付け列を追加する。
-- AlterTable
ALTER TABLE "users" DROP COLUMN "password_hash",
ADD COLUMN     "auth_user_id" UUID;

-- CreateIndex
CREATE UNIQUE INDEX "users_auth_user_id_key" ON "users"("auth_user_id");
