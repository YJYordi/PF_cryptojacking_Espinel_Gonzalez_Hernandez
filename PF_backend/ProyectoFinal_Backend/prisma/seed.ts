

import * as path from 'path';
import * as dotenv from 'dotenv';

dotenv.config({
  path: path.resolve(__dirname, '../.env'),
});

import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  const rules = [
    { type: 'DOMAIN_IOC', pattern: 'minexmr', description: 'XMR pool', enabled: true },
    { type: 'DOMAIN_IOC', pattern: 'hashvault', description: 'Hashvault pool', enabled: true },
    { type: 'DOMAIN_IOC', pattern: 'nanopool', description: 'Nanopool', enabled: true },
    { type: 'DOMAIN_IOC', pattern: 'supportxmr', description: 'SupportXMR', enabled: true },
  ];

  for (const r of rules) {
    // Buscar si ya existe
    const existing = await prisma.rule.findFirst({
      where: {
        type: r.type,
        pattern: r.pattern,
      },
    });

    if (existing) {
      // Actualizar si existe
      await prisma.rule.update({
        where: { id: existing.id },
        data: {
          description: r.description,
          enabled: r.enabled,
        },
      });
    } else {
      // Crear si no existe
      await prisma.rule.create({
        data: {
          type: r.type,
          pattern: r.pattern,
          description: r.description,
          enabled: r.enabled,
          tags: [],
        },
      });
    }
  }

  console.log('Seed rules done');
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
