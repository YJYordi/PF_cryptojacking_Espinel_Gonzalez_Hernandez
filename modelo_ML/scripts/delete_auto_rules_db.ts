#!/usr/bin/env ts-node
/**
 * Script para eliminar reglas generadas automáticamente desde la base de datos
 * Deja solo las reglas del seed (sin tag 'auto-generated')
 */

import { PrismaClient } from '@prisma/client';
import * as dotenv from 'dotenv';
import * as path from 'path';

// Cargar variables de entorno
const envPath = path.resolve(__dirname, '../../../PF_backend/ProyectoFinal_Backend/.env');
dotenv.config({ path: envPath });

const prisma = new PrismaClient();

async function main() {
  console.log('==========================================');
  console.log('Eliminando reglas generadas automáticamente');
  console.log('==========================================');
  console.log('');

  try {
    // Buscar todas las reglas con tag 'auto-generated'
    const autoRules = await prisma.rule.findMany({
      where: {
        tags: {
          has: 'auto-generated'
        }
      }
    });

    console.log(`Reglas encontradas con tag 'auto-generated': ${autoRules.length}`);

    if (autoRules.length === 0) {
      console.log('✅ No hay reglas auto-generadas para eliminar');
      return;
    }

    // Mostrar resumen
    console.log('\nReglas que se eliminarán:');
    autoRules.forEach((rule, i) => {
      console.log(`  ${i + 1}. ${rule.name || rule.pattern} (ID: ${rule.id})`);
    });

    // Eliminar reglas
    const result = await prisma.rule.deleteMany({
      where: {
        tags: {
          has: 'auto-generated'
        }
      }
    });

    console.log(`\n✅ Eliminadas ${result.count} reglas generadas automáticamente`);

    // Verificar reglas del seed que quedan
    const seedRules = await prisma.rule.findMany({
      where: {
        tags: {
          isEmpty: true  // Las reglas del seed no tienen tags
        }
      }
    });

    console.log(`\n📋 Reglas del seed que permanecen: ${seedRules.length}`);
    seedRules.forEach((rule, i) => {
      console.log(`  ${i + 1}. ${rule.pattern} - ${rule.description || 'Sin descripción'}`);
    });

    console.log('\n✅ Proceso completado');
  } catch (error) {
    console.error('❌ Error al eliminar reglas:', error);
    process.exit(1);
  } finally {
    await prisma.$disconnect();
  }
}

main();

