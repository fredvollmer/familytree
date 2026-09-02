import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const inputPath = new URL("../Fredric_Vollmer_Maternal_Family_Tree_Records_First_Index.xlsx", import.meta.url).pathname;
const previewDir = new URL("../workbook-previews/original/", import.meta.url).pathname;

const input = await FileBlob.load(inputPath);
const workbook = await SpreadsheetFile.importXlsx(input);
const summary = await workbook.inspect({
  kind: "workbook,sheet,table",
  maxChars: 12000,
  tableMaxRows: 8,
  tableMaxCols: 12,
  tableMaxCellChars: 100,
});
console.log(summary.ndjson ?? summary);

await fs.mkdir(previewDir, { recursive: true });
for (const sheet of workbook.worksheets.items) {
  const preview = await workbook.render({
    sheetName: sheet.name,
    autoCrop: "all",
    scale: 1,
    format: "png",
  });
  const safeName = sheet.name.replace(/[^a-z0-9_-]+/gi, "_");
  await fs.writeFile(`${previewDir}/${safeName}.png`, new Uint8Array(await preview.arrayBuffer()));
}
