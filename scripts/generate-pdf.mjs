#!/usr/bin/env node
/**
 * Generate ATS-optimized PDF from HTML template.
 *
 * Usage: node scripts/generate-pdf.mjs <input.html> <output.pdf> [--format=a4|letter]
 */
import { chromium } from 'playwright';
import { readFile } from 'fs/promises';
import { resolve, dirname } from 'path';
import { normalizeTextForATS } from './normalize-ats.mjs';

const [,, inputPath, outputPath, ...flags] = process.argv;

if (!inputPath || !outputPath) {
  console.error('Usage: node scripts/generate-pdf.mjs <input.html> <output.pdf> [--format=a4|letter]');
  process.exit(1);
}

const format = flags.find(f => f.startsWith('--format='))?.split('=')[1] || 'letter';
const width = format === 'a4' ? '210mm' : '8.5in';
const height = format === 'a4' ? '297mm' : '11in';

async function main() {
  // Read and normalize HTML
  let html = await readFile(resolve(inputPath), 'utf-8');

  // Rewrite relative font paths to absolute file:// URLs
  const htmlDir = dirname(resolve(inputPath));
  html = html.replace(/url\(['"]?\.\/fonts\//g, `url('file://${htmlDir}/fonts/`);

  // ATS normalization
  html = normalizeTextForATS(html);

  // Launch headless Chromium
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.setContent(html, { waitUntil: 'networkidle' });

  // Wait for fonts to load
  await page.evaluate(() => document.fonts.ready);

  // Generate PDF
  await page.pdf({
    path: resolve(outputPath),
    width,
    height,
    margin: { top: '0.6in', right: '0.6in', bottom: '0.6in', left: '0.6in' },
    printBackground: true,
    preferCSSPageSize: false,
  });

  await browser.close();
  console.log(`PDF generated: ${outputPath}`);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
