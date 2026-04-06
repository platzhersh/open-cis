-- AlterTable
ALTER TABLE "User" ADD COLUMN "externalId" TEXT;

-- Backfill existing rows with a unique placeholder
UPDATE "User" SET "externalId" = 'legacy-' || "id" WHERE "externalId" IS NULL;

-- Make the column required and unique
ALTER TABLE "User" ALTER COLUMN "externalId" SET NOT NULL;

-- CreateIndex
CREATE UNIQUE INDEX "User_externalId_key" ON "User"("externalId");
