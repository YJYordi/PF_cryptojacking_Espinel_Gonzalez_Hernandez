-- DropForeignKey
ALTER TABLE "public"."Alert" DROP CONSTRAINT "Alert_flowId_fkey";

-- DropIndex
DROP INDEX "public"."Alert_createdAt_idx";

-- AlterTable
ALTER TABLE "Alert" ALTER COLUMN "flowId" DROP NOT NULL;

-- AddForeignKey
ALTER TABLE "Alert" ADD CONSTRAINT "Alert_flowId_fkey" FOREIGN KEY ("flowId") REFERENCES "Flow"("id") ON DELETE SET NULL ON UPDATE CASCADE;
