import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const packageDir = new URL("../", import.meta.url).pathname;
const projectDir = new URL("../../../../", import.meta.url).pathname;
const outputDir = `${projectDir}outputs/01a06308-afa6-7520-af69-eb57d94d77c3`;
const inputPath = `${packageDir}Fredric_Vollmer_Maternal_Family_Tree_Records_First_Index.xlsx`;
const outputName = "Fredric_Vollmer_Complete_Family_Tree_Index.xlsx";

const input = await FileBlob.load(inputPath);
const workbook = await SpreadsheetFile.importXlsx(input);

for (const [fileName, sheetName] of [
  ["Fredric_Vollmer_Complete_Family_Tree_People.csv", "Consolidated People"],
  ["Fredric_Vollmer_Complete_Family_Tree_Families.csv", "Consolidated Families"],
  ["Fredric_Vollmer_Complete_Family_Tree_Source_Inventory.csv", "Consolidated Sources"],
  ["Fredric_Vollmer_Complete_Family_Tree_Vital_Date_Coverage.csv", "Vital Date Coverage"],
  ["Fredric_Vollmer_Complete_Family_Tree_Occupation_Coverage.csv", "Occupation Coverage"],
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
overview.getRange("A5:A14").values = [
  ["Individuals"],
  ["Families"],
  ["GEDCOM source records"],
  ["Source and record inventory items"],
  ["Birth dates recorded"],
  ["Death dates recorded"],
  ["Both vital dates recorded"],
  ["No dated event: unresolved or private"],
  ["People with a recorded occupation or role"],
  ["Accepted occupation or role events"],
];
overview.getRange("B5").formulas = [["=COUNTA('Consolidated People'!$A$2:$A$329)"]];
overview.getRange("B6").formulas = [["=COUNTA('Consolidated Families'!$A$2:$A$156)"]];
overview.getRange("B7").formulas = [["=COUNTA('Consolidated Sources'!$A$2:$A$92)-COUNTIF('Consolidated Sources'!$F$2:$F$92,\"preserved original or derivative record\")"]];
overview.getRange("B8").formulas = [["=COUNTA('Consolidated Sources'!$A$2:$A$92)"]];
overview.getRange("B9").formulas = [["=COUNTIF('Vital Date Coverage'!$D$2:$D$329,\"recorded\")"]];
overview.getRange("B10").formulas = [["=COUNTIF('Vital Date Coverage'!$F$2:$F$329,\"recorded\")"]];
overview.getRange("B11").formulas = [["=COUNTIF('Vital Date Coverage'!$G$2:$G$329,\"complete\")"]];
overview.getRange("B12").formulas = [["=COUNTIF('Vital Date Coverage'!$G$2:$G$329,\"unresolved\")+COUNTIF('Vital Date Coverage'!$G$2:$G$329,\"not researched—privacy limited\")+COUNTIF('Vital Date Coverage'!$G$2:$G$329,\"withheld—living/private\")"]];
overview.getRange("B13").formulas = [["=COUNTIF('Occupation Coverage'!$E$2:$E$329,\"recorded\")"]];
overview.getRange("B14").formulas = [["=COUNTIF('Occupation Coverage'!$D$2:$D$329,\"1\")+2*COUNTIF('Occupation Coverage'!$D$2:$D$329,\"2\")+3*COUNTIF('Occupation Coverage'!$D$2:$D$329,\"3\")"]];

overview.getRange("D4:F4").values = [["Controlling correction", "Status", "Treatment"]];
overview.getRange("D5:D11").values = [
  ["Jan is Fredric's biological mother"],
  ["Mary Alice Thoren identity and parents"],
  ["Jan is Chris Vollmer's stepmother"],
  ["Chris's father"],
  ["Janet Chaffee transcription"],
  ["Bruce Eric Muller vital dates"],
  ["Peter Vollmer identity and dates"],
];
overview.getRange("E5").formulas = [["=IF(COUNTIF('Consolidated People'!$B$2:$B$329,\"Jan Muller Vollmer\")=1,\"Confirmed\",\"Review\")"]];
overview.getRange("E6").formulas = [["=IF(COUNTIF('Consolidated People'!$B$2:$B$329,\"Mary Alice Thoren\")=1,\"Confirmed\",\"Review\")"]];
overview.getRange("E7:E11").values = [["Confirmed"], ["Confirmed"], ["Removed"], ["Recorded with conflict"], ["Consolidated"]];
overview.getRange("F5:F11").values = [
  ["Biological parent link in GEDCOM family F095"],
  ["Port Townsend birthplace; William and Alice parent links; William's proven Swedish ancestry added; Alice's parents remain unresolved"],
  ["Step relationship recorded; not a biological parent link"],
  ["Henry and Mary Alice are the biological parents; Chris is Fredric's paternal half-brother"],
  ["Corrected to James Chaffee throughout the consolidated tree"],
  ["15 Jun 1958–4 Jun 1972; Vancouver hospital death; family age-14 recollection retained"],
  ["29 Jun 1959–5 Aug 1975; Henry named as father; Christopher named as sibling; mother unresolved"],
];

overview.getRange("A16:F16").values = [["Package component", "Role", "Rows / items", "Primary file", "Status", "Notes"]];
overview.getRange("A17:F24").values = [
  ["GEDCOM", "Canonical tree structure", 328, "Fredric_Vollmer_Complete_Family_Tree.ged", "Current", "Import this file into genealogy software"],
  ["Canonical JSON", "Structured mirror", 328, "Fredric_Vollmer_Complete_Family_Tree_Canonical_Data.json", "Current", "Machine-readable people, families, and sources"],
  ["People ledger", "Person-level audit", 328, "Fredric_Vollmer_Complete_Family_Tree_People.csv", "Current", "One row per GEDCOM individual"],
  ["Families ledger", "Family-level audit", 155, "Fredric_Vollmer_Complete_Family_Tree_Families.csv", "Current", "Parent, spouse, child, and marriage links"],
  ["Sources ledger", "Citation and record index", 91, "Fredric_Vollmer_Complete_Family_Tree_Source_Inventory.csv", "Current", "Includes 48 GEDCOM sources and 43 preserved record files"],
  ["Vital-date coverage", "Birth/death status for every person", 328, "Fredric_Vollmer_Complete_Family_Tree_Vital_Date_Coverage.csv", "Current", "Recorded, unresolved, or privacy-limited outcome for every person"],
  ["Occupation coverage", "Occupation/role status for every person", 328, "Fredric_Vollmer_Complete_Family_Tree_Occupation_Coverage.csv", "Current", "17 people with 23 cited events; every other person has an explicit coverage outcome"],
  ["Recovered workbook tabs", "Historical reference", 8, "Original tabs in this workbook", "Preserved", "Retained unchanged for provenance"],
];

const navy = "#17365D";
const blue = "#D9E7F5";
const pale = "#F3F7FB";
const green = "#E2F0D9";
overview.getRange("A1:F24").format.font = { name: "Aptos", size: 10 };
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
for (const address of ["A4:B4", "D4:F4", "A16:F16"]) {
  overview.getRange(address).format = {
    fill: navy,
    font: { bold: true, color: "#FFFFFF" },
    verticalAlignment: "center",
  };
}
overview.getRange("A5:B14").format.fill = pale;
overview.getRange("B5:B14").format = { font: { bold: true, color: navy }, horizontalAlignment: "right", numberFormat: "0" };
overview.getRange("D5:F11").format = { fill: pale, wrapText: true, verticalAlignment: "top" };
overview.getRange("E5:E8").format.fill = green;
overview.getRange("A17:F24").format = { wrapText: true, verticalAlignment: "top" };
overview.getRange("A17:F24").conditionalFormats.addCustom("=MOD(ROW(),2)=0", { fill: "#EAF3F8" });
overview.getRange("A1:F1").format.font = { name: "Aptos Display", size: 16, bold: true, color: "#FFFFFF" };
overview.getRange("A2:F2").format.font = { name: "Aptos", size: 11, bold: true, color: navy };
overview.getRange("A1:F1").format.rowHeight = 28;
overview.getRange("A2:F2").format.rowHeight = 36;
overview.getRange("A4:F24").format.rowHeight = 28;
overview.getRange("A17:F24").format.rowHeight = 46;
overview.getRange("A1:A24").format.columnWidth = 29;
overview.getRange("B1:B24").format.columnWidth = 24;
overview.getRange("C1:C24").format.columnWidth = 13;
overview.getRange("D1:D24").format.columnWidth = 46;
overview.getRange("E1:E24").format.columnWidth = 19;
overview.getRange("F1:F24").format.columnWidth = 50;
overview.freezePanes.freezeRows(2);

const configs = [
  { name: "Consolidated People", table: "ConsolidatedPeopleTable", widths: [14, 32, 7, 30, 30, 66, 30, 26, 72, 18, 24] },
  { name: "Consolidated Families", table: "ConsolidatedFamiliesTable", widths: [14, 14, 14, 48, 30, 72, 28] },
  { name: "Consolidated Sources", table: "ConsolidatedSourcesTable", widths: [18, 46, 26, 16, 80, 28] },
  { name: "Vital Date Coverage", table: "VitalDateCoverageTable", widths: [14, 32, 30, 35, 30, 35, 32, 28] },
  { name: "Occupation Coverage", table: "OccupationCoverageTable", widths: [14, 32, 78, 13, 38, 26, 26, 26, 72] },
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
  sheet.freezePanes.freezeColumns(["Consolidated People", "Vital Date Coverage", "Occupation Coverage"].includes(config.name) ? 2 : 1);
}

const coverage = workbook.worksheets.getItem("Vital Date Coverage");
coverage.getRange("G2:G329").conditionalFormats.addCustom('=$G2="complete"', { fill: green });
coverage.getRange("G2:G329").conditionalFormats.addCustom('=$G2="partial"', { fill: "#FFF2CC" });
coverage.getRange("G2:G329").conditionalFormats.addCustom('=OR($G2="unresolved",$G2="not researched—privacy limited",$G2="withheld—living/private")', { fill: "#FCE4D6" });

const occupationCoverage = workbook.worksheets.getItem("Occupation Coverage");
occupationCoverage.getRange("E2:E329").conditionalFormats.addCustom('=$E2="recorded"', { fill: green });
occupationCoverage.getRange("E2:E329").conditionalFormats.addCustom('=OR($E2="unresolved—no supported occupation found",$E2="not researched—privacy limited",$E2="withheld—living/private",$E2="not established—minor")', { fill: "#FCE4D6" });

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
