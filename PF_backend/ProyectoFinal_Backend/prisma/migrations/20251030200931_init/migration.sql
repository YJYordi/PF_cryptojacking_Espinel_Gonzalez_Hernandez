-- CreateTable
CREATE TABLE "Host" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "labels" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Host_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Flow" (
    "id" TEXT NOT NULL,
    "hostId" TEXT NOT NULL,
    "fiveTuple" TEXT NOT NULL,
    "sni" TEXT,
    "ja3" TEXT,
    "tsStart" TIMESTAMP(3) NOT NULL,
    "tsEnd" TIMESTAMP(3),
    "bytesIn" INTEGER NOT NULL DEFAULT 0,
    "bytesOut" INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT "Flow_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Feature" (
    "flowId" TEXT NOT NULL,
    "v" JSONB NOT NULL,

    CONSTRAINT "Feature_pkey" PRIMARY KEY ("flowId")
);

-- CreateTable
CREATE TABLE "Score" (
    "id" TEXT NOT NULL,
    "flowId" TEXT NOT NULL,
    "model" TEXT NOT NULL,
    "score" DOUBLE PRECISION NOT NULL,
    "version" TEXT NOT NULL DEFAULT '1',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Score_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Alert" (
    "id" TEXT NOT NULL,
    "flowId" TEXT NOT NULL,
    "severity" TEXT NOT NULL,
    "reason" JSONB NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Alert_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Rule" (
    "id" TEXT NOT NULL,
    "vendor" TEXT NOT NULL,
    "sid" INTEGER NOT NULL,
    "name" TEXT NOT NULL,
    "body" TEXT NOT NULL,
    "enabled" BOOLEAN NOT NULL DEFAULT true,
    "tags" TEXT[],
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Rule_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Event" (
    "id" TEXT NOT NULL,
    "hostId" TEXT NOT NULL,
    "kind" TEXT NOT NULL,
    "payload" JSONB NOT NULL,
    "ts" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Event_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "Flow_hostId_tsStart_idx" ON "Flow"("hostId", "tsStart");

-- CreateIndex
CREATE INDEX "Flow_sni_idx" ON "Flow"("sni");

-- CreateIndex
CREATE INDEX "Flow_ja3_idx" ON "Flow"("ja3");

-- CreateIndex
CREATE INDEX "Score_flowId_createdAt_idx" ON "Score"("flowId", "createdAt");

-- CreateIndex
CREATE INDEX "Alert_createdAt_idx" ON "Alert"("createdAt");

-- CreateIndex
CREATE INDEX "Event_hostId_ts_idx" ON "Event"("hostId", "ts");

-- AddForeignKey
ALTER TABLE "Flow" ADD CONSTRAINT "Flow_hostId_fkey" FOREIGN KEY ("hostId") REFERENCES "Host"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Feature" ADD CONSTRAINT "Feature_flowId_fkey" FOREIGN KEY ("flowId") REFERENCES "Flow"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Score" ADD CONSTRAINT "Score_flowId_fkey" FOREIGN KEY ("flowId") REFERENCES "Flow"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Alert" ADD CONSTRAINT "Alert_flowId_fkey" FOREIGN KEY ("flowId") REFERENCES "Flow"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Event" ADD CONSTRAINT "Event_hostId_fkey" FOREIGN KEY ("hostId") REFERENCES "Host"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
