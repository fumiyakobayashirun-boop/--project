-- CreateEnum
CREATE TYPE "member_type" AS ENUM ('local_player', 'user');

-- CreateEnum
CREATE TYPE "visibility" AS ENUM ('public', 'followers_only');

-- CreateEnum
CREATE TYPE "registered_by" AS ENUM ('self', 'pathstone');

-- CreateEnum
CREATE TYPE "contact_type" AS ENUM ('email', 'line', 'sns', 'discord');

-- CreateTable
CREATE TABLE "users" (
    "id" UUID NOT NULL,
    "member_type" "member_type" NOT NULL,
    "email" TEXT NOT NULL,
    "password_hash" TEXT NOT NULL,
    "display_name" TEXT NOT NULL,
    "activity_description" TEXT,
    "challenge_description" TEXT,
    "motivation_description" TEXT,
    "location_label" TEXT,
    "latitude" DOUBLE PRECISION,
    "longitude" DOUBLE PRECISION,
    "visibility" "visibility" NOT NULL DEFAULT 'public',
    "registered_by" "registered_by" NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "categories" (
    "id" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "sort_order" INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT "categories_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "user_categories" (
    "user_id" UUID NOT NULL,
    "category_id" UUID NOT NULL,

    CONSTRAINT "user_categories_pkey" PRIMARY KEY ("user_id","category_id")
);

-- CreateTable
CREATE TABLE "contact_methods" (
    "id" UUID NOT NULL,
    "user_id" UUID NOT NULL,
    "contact_type" "contact_type" NOT NULL,
    "value" TEXT NOT NULL,
    "label" TEXT,
    "display_order" INTEGER,

    CONSTRAINT "contact_methods_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "follows" (
    "id" UUID NOT NULL,
    "follower_id" UUID NOT NULL,
    "followee_id" UUID NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "follows_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "contact_logs" (
    "id" UUID NOT NULL,
    "actor_id" UUID,
    "target_id" UUID NOT NULL,
    "contact_method_id" UUID NOT NULL,
    "is_anonymous" BOOLEAN NOT NULL DEFAULT false,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "contact_logs_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "users_email_key" ON "users"("email");

-- CreateIndex
CREATE UNIQUE INDEX "categories_name_key" ON "categories"("name");

-- CreateIndex
CREATE UNIQUE INDEX "follows_follower_id_followee_id_key" ON "follows"("follower_id", "followee_id");

-- AddForeignKey
ALTER TABLE "user_categories" ADD CONSTRAINT "user_categories_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "user_categories" ADD CONSTRAINT "user_categories_category_id_fkey" FOREIGN KEY ("category_id") REFERENCES "categories"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "contact_methods" ADD CONSTRAINT "contact_methods_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "follows" ADD CONSTRAINT "follows_follower_id_fkey" FOREIGN KEY ("follower_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "follows" ADD CONSTRAINT "follows_followee_id_fkey" FOREIGN KEY ("followee_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "contact_logs" ADD CONSTRAINT "contact_logs_actor_id_fkey" FOREIGN KEY ("actor_id") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "contact_logs" ADD CONSTRAINT "contact_logs_target_id_fkey" FOREIGN KEY ("target_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "contact_logs" ADD CONSTRAINT "contact_logs_contact_method_id_fkey" FOREIGN KEY ("contact_method_id") REFERENCES "contact_methods"("id") ON DELETE CASCADE ON UPDATE CASCADE;
