import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const packageDir = new URL("../", import.meta.url).pathname;
const projectDir = new URL("../../../../", import.meta.url).pathname;
const outputDir = `${projectDir}outputs/01a062d4-f2da-7773-8314-870803324d29`;
const inputPath = `${packageDir}Fredric_Vollmer_Maternal_Family_Tree_Records_First_Index.xlsx`;
const outputName = "Fredric_Vollmer_Complete_Family_Tree_Index.xlsx";

const input = await FileBlob.load(inputPath);
const workbook = await SpreadsheetFile.importXlsx(input);

for (const [fileName, sheetName] of [
  ["Fredric_Vollmer_Complete_Family_Tree_People.csv", "Consolidated People"],
  ["Fredric_Vollmer_Complete_Family_Tree_Families.csv", "Consolidated Families"],
  ["Fredric_Vollmer_Complete_Family_Tree_Source_Inventory.csv", "Consolidated Sources"],
]) {
  const csvText = await fs.readFile(`${packageDir}${fileName}`, "utf8");
  await workbook.fromCSV(csvText, { sheetName });
}

const overview = workbook.worksheets.add("Consolidated Overview");
overview.showGridLines = false;
overview.getRange("A1:F1").merge();
overview.getRange("A1").values = [["Fredric Vollmer Complete Family Tree — Consolidated Index"]];
overview.getRange("A2:F2").merge();
overview.getRange("A2").values = [["One source-of-truth package assembled from the standardized maternal tree and all completed project-chat research"]];
overview.getRange("A4:B4").values = [["Tree metric", "Current value"]];
overview.getRange("A5:A8").values = [["Individuals"], ["Families"], ["GEDCOM source records"], ["Source and record inventory items"]];
overview.getRange("B5").formulas = [["=COUNTA('Consolidated People'!$A$2:$A$328)"]];
overview.getRange("B6").formulas = [["=COUNTA('Consolidated Families'!$A$2:$A$155)"]];
overview.getRange("B7").formulas = [["=COUNTA('Consolidated Sources'!$A$2:$A$46)"]];
overview.getRange("B8").formulas = [["=COUNTA('Consolidated Sources'!$A$2:$A$89)"]];

overview.getRange("D4:F4").values = [["Controlling correction", "Status", "Treatment"]];
overview.getRange("D5:D9").values = [
  ["Jan is Fredric's biological mother"],
  ["Mary Alice Thoren identity and parents"],
  ["Jan is Chris Vollmer's stepmother"],
  ["Chris's father"],
  ["Janet Chaffee transcription"],
];
overview.getRange("E5").formulas = [["=IF(COUNTIF('Consolidated People'!$B$2:$B$328,\"Jan Muller Vollmer\")=1,\"Confirmed\",\"Review\")"]];
overview.getRange("E6").formulas = [["=IF(COUNTIF('Consolidated People'!$B$2:$B$328,\"Mary Alice Thoren\")=1,\"Confirmed\",\"Review\")"]];
overview.getRange("E7:E9").values = [["Confirmed"], ["Confirmed"], ["Removed"]];
overview.getRange("F5:F9").values = [
  ["Biological parent link in GEDCOM family F095"],
  ["Port Townsend birthplace; William and Alice parent links; William's proven Swedish ancestry added; Alice's parents remain unresolved"],
  ["Step relationship recorded; not a biological parent link"],
  ["Henry and Mary Alice are the biological parents; Chris is Fredric's paternal half-brother"],
  ["Corrected to James Chaffee throughout the consolidated tree"],
];

overview.getRange("A11:F11").values = [["Package component", "Role", "Rows / items", "Primary file", "Status", "Notes"]];
overview.getRange("A12:F17").values = [
  ["GEDCOM", "Canonical tree structure", 327, "Fredric_Vollmer_Complete_Family_Tree.ged", "Current", "Import this file into genealogy software"],
  ["Canonical JSON", "Structured mirror", 327, "Fredric_Vollmer_Complete_Family_Tree_Canonical_Data.json", "Current", "Machine-readable people, families, and sources"],
  ["People ledger", "Person-level audit", 327, "Fredric_Vollmer_Complete_Family_Tree_People.csv", "Current", "One row per GEDCOM individual"],
  ["Families ledger", "Family-level audit", 154, "Fredric_Vollmer_Complete_Family_Tree_Families.csv", "Current", "Parent, spouse, child, and marriage links"],
  ["Sources ledger", "Citation and record index", 88, "Fredric_Vollmer_Complete_Family_Tree_Source_Inventory.csv", "Current", "Includes 45 GEDCOM sources and 43 preserved record files"],
  ["Recovered workbook tabs", "Historical reference", 8, "Original tabs in this workbook", "Preserved", "Retained unchanged for provenance"],
];

const navy = "#17365D";
const blue = "#D9E7F5";
const pale = "#F3F7FB";
const green = "#E2F0D9";
overview.getRange("A1:F17").format.font = { name: "Aptos", size: 10 };
overview.getRange("A1:F1").format = {
  fill: navy,
  font: { bold: true, color: "#FFFFFF", size: 16 },
  verticalAlignment: "center",
};
overview.getRange("A2:F2").format = {
  fill: blue,
  font: { bold: true, color: navy, size: 11 },
  wrapText: true,
};
for (const address of ["A4:B4", "D4:F4", "A11:F11"]) {
  overview.getRange(address).format = {
    fill: navy,
    font: { bold: true, color: "#FFFFFF" },
    verticalAlignment: "center",
  };
}
overview.getRange("A5:B8").format.fill = pale;
overview.getRange("B5:B8").format = { font: { bold: true, color: navy }, horizontalAlignment: "right", numberFormat: "0" };
overview.getRange("D5:F9").format = { fill: pale, wrapText: true, verticalAlignment: "top" };
overview.getRange("E5:E8").format.fill = green;
overview.getRange("A12:F17").format = { wrapText: true, verticalAlignment: "top" };
overview.getRange("A12:F17").conditionalFormats.addCustom("=MOD(ROW(),2)=0", { fill: "#EAF3F8" });
overview.getRange("A1:F1").format.font = { name: "Aptos Display", size: 16, bold: true, color: "#FFFFFF" };
overview.getRange("A2:F2").format.font = { name: "Aptos", size: 11, bold: true, color: navy };
overview.getRange("A1:F1").format.rowHeight = 28;
overview.getRange("A2:F2").format.rowHeight = 36;
overview.getRange("A4:F17").format.rowHeight = 28;
overview.getRange("A12:F17").format.rowHeight = 46;
overview.getRange("A1:A17").format.columnWidth = 29;
overview.getRange("B1:B17").format.columnWidth = 24;
overview.getRange("C1:C17").format.columnWidth = 13;
overview.getRange("D1:D17").format.columnWidth = 46;
overview.getRange("E1:E17").format.columnWidth = 19;
overview.getRange("F1:F17").format.columnWidth = 50;
overview.freezePanes.freezeRows(2);

const configs = [
  { name: "Consolidated People", table: "ConsolidatedPeopleTable", widths: [14, 32, 7, 30, 30, 30, 26, 72, 18, 24] },
  { name: "Consolidated Families", table: "ConsolidatedFamiliesTable", widths: [14, 14, 14, 48, 30, 72, 28] },
  { name: "Consolidated Sources", table: "ConsolidatedSourcesTable", widths: [18, 46, 26, 16, 80, 28] },
];
for (const config of configs) {
  const sheet = workbook.worksheets.getItem(config.name);
  sheet.showGridLines = false;
  const used = sheet.getUsedRange();
  used.format.font = { name: "Aptos", size: 10 };
  used.format.verticalAlignment = "top";
  used.format.wrapText = true;
  const table = sheet.tables.add(used, true, config.table);
  table.style = "TableStyleMedium2";
  table.showBandedRows = true;
  table.showFilterButton = true;
  sheet.getRangeByIndexes(0, 0, 1, config.widths.length).format = {
    fill: navy,
    font: { name: "Aptos", size: 10, bold: true, color: "#FFFFFF" },
    rowHeight: 30,
    verticalAlignment: "center",
    wrapText: true,
  };
  config.widths.forEach((width, index) => {
    sheet.getRangeByIndexes(0, index, used.rowCount, 1).format.columnWidth = width;
  });
  sheet.freezePanes.freezeRows(1);
  sheet.freezePanes.freezeColumns(config.name === "Consolidated People" ? 2 : 1);
}

await fs.mkdir(outputDir, { recursive: true });
const exported = await SpreadsheetFile.exportXlsx(workbook);
await exported.save(`${outputDir}/${outputName}`);
await exported.save(`${packageDir}${outputName}`);

const inspect = await workbook.inspect({
  kind: "workbook,sheet,table,formula",
  maxChars: 18000,
  tableMaxRows: 5,
  tableMaxCols: 10,
  tableMaxCellChars: 100,
  options: { maxResults: 80 },
});
console.log(inspect.ndjson ?? inspect);

const previewDir = `${packageDir}workbook-previews/consolidated`;
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
