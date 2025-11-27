/*
  Warnings:

  - You are about to drop the column `body` on the `Rule` table. All the data in the column will be lost.
  - You are about to drop the column `name` on the `Rule` table. All the data in the column will be lost.
  - You are about to drop the column `sid` on the `Rule` table. All the data in the column will be lost.
  - You are about to drop the column `vendor` on the `Rule` table. All the data in the column will be lost.
  - A unique constraint covering the columns `[name]` on the table `Host` will be added. If there are existing duplicate values, this will fail.
  - A unique constraint covering the columns `[type,pattern]` on the table `Rule` will be added. If there are existing duplicate values, this will fail.
  - Added the required column `pattern` to the `Rule` table without a default value. This is not possible if the table is not empty.
  - Added the required column `type` to the `Rule` table without a default value. This is not possible if the table is not empty.

*/
-- AlterTable
ALTER TABLE "Rule" DROP COLUMN "body",
DROP COLUMN "name",
DROP COLUMN "sid",
DROP COLUMN "vendor",
ADD COLUMN     "description" TEXT,
ADD COLUMN     "pattern" TEXT NOT NULL,
ADD COLUMN     "type" TEXT NOT NULL;

-- CreateIndex
CREATE UNIQUE INDEX "Host_name_key" ON "Host"("name");

-- CreateIndex
CREATE UNIQUE INDEX "Rule_type_pattern_key" ON "Rule"("type", "pattern");
