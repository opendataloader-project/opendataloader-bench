// liteparse_runner.js
import { LiteParse } from "@llamaindex/liteparse";

const pdfPath = process.argv[2];
if (!pdfPath) {
  process.stderr.write("Usage: node liteparse_runner.js <pdf_path>\n");
  process.exit(1);
}

const parser = new LiteParse({ ocrEnabled: false });
const result = await parser.parse(pdfPath);
process.stdout.write(result.text);
