import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const workbookPath = new URL("../Fredric_Vollmer_Complete_Family_Tree_Index.xlsx", import.meta.url).pathname;
const input = await FileBlob.load(workbookPath);
const workbook = await SpreadsheetFile.importXlsx(input);
const errors = [];
const sheets = [];

for (const sheet of workbook.worksheets.items) {
  const used = sheet.getUsedRange();
  const values = used.values;
  const formulas = used.formulas;
  sheets.push({ name: sheet.name, rows: used.rowCount, columns: used.columnCount });
  for (let row = 0; row < values.length; row += 1) {
    for (let col = 0; col < values[row].length; col += 1) {
      const text = String(values[row][col] ?? "");
      if (/^#(?:REF!|DIV\/0!|VALUE!|NAME\?|N\/A|NUM!|NULL!)/.test(text)) {
        errors.push(`${sheet.name} R${row + 1}C${col + 1}: ${text}`);
      }
    }
  }
  if (!Array.isArray(formulas)) {
    errors.push(`${sheet.name}: formulas could not be inspected`);
  }
}

const overview = workbook.worksheets.getItem("Consolidated Overview");
const overviewValues = overview.getRange("A1:F17").values;
const expected = { individuals: 310, families: 146, sources: 33, inventory: 76 };
const actual = {
  individuals: overviewValues[4][1],
  families: overviewValues[5][1],
  sources: overviewValues[6][1],
  inventory: overviewValues[7][1],
};
for (const key of Object.keys(expected)) {
  if (actual[key] !== expected[key]) errors.push(`Overview ${key}: expected ${expected[key]}, got ${actual[key]}`);
}

console.log(JSON.stringify({ sheets, overview: actual, formulaErrors: errors }, null, 2));
if (errors.length) process.exitCode = 1;
