-- DropForeignKey
ALTER TABLE "public"."Alert" DROP CONSTRAINT IF EXISTS "Alert_flowId_fkey";

-- AlterTable
-- Eliminamos la columna flowId si existe
ALTER TABLE "public"."Alert" DROP COLUMN IF EXISTS "flowId";

-- Agregamos la nueva columna eventId (temporalmente nullable para migración)
ALTER TABLE "public"."Alert" ADD COLUMN "eventId" TEXT;

-- Si hay datos existentes sin eventId, los eliminamos (ya que no tienen sentido sin evento)
DELETE FROM "public"."Alert" WHERE "eventId" IS NULL;

-- Ahora hacemos eventId NOT NULL
ALTER TABLE "public"."Alert" ALTER COLUMN "eventId" SET NOT NULL;

-- AddForeignKey
ALTER TABLE "public"."Alert" ADD CONSTRAINT "Alert_eventId_fkey" FOREIGN KEY ("eventId") REFERENCES "Event"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

