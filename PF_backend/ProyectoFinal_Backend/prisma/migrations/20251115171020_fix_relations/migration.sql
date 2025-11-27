/*
  Warnings:

  - Made the column `labels` on table `Host` required. This step will fail if there are existing NULL values in that column.

*/
-- DropIndex
DROP INDEX "public"."Host_name_key";

-- DropIndex
DROP INDEX "public"."Rule_type_pattern_key";

-- AlterTable
ALTER TABLE "Host" ADD COLUMN     "lastSeen" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
ALTER COLUMN "labels" SET NOT NULL;

-- AlterTable
ALTER TABLE "Rule" ADD COLUMN     "body" TEXT,
ADD COLUMN     "name" TEXT,
ADD COLUMN     "sid" INTEGER,
ADD COLUMN     "vendor" TEXT;
