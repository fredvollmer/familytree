import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const [inputPath, outputDir, startAtArg = "0"] = process.argv.slice(2);
if (!inputPath || !outputDir) {
  throw new Error("usage: render_index_artifact_tool.mjs INPUT_XLSX OUTPUT_DIR [ZERO_BASED_START_INDEX]");
}
const startAt = Number.parseInt(startAtArg, 10);
if (!Number.isInteger(startAt) || startAt < 0) throw new Error("start index must be a non-negative integer");

await fs.mkdir(outputDir, { recursive: true });
const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(inputPath));
const names = [];
for (let index = startAt; ; index += 1) {
  let sheet;
  try {
    sheet = workbook.worksheets.getItemAt(index);
  } catch {
    break;
  }
  if (!sheet) break;
  const name = sheet.name;
  names.push(name);
  const preview = await workbook.render({ sheetName: name, autoCrop: "all", scale: 0.8, format: "png" });
  const safeName = name.replace(/[^A-Za-z0-9._-]+/g, "_");
  await fs.writeFile(path.join(outputDir, `${String(index + 1).padStart(2, "0")}_${safeName}.png`), new Uint8Array(await preview.arrayBuffer()));
}
console.log(JSON.stringify(names));
