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
const expected = { individuals: 327, families: 154, sources: 45, inventory: 88 };
const actual = {
  individuals: overviewValues[4][1],
  families: overviewValues[5][1],
  sources: overviewValues[6][1],
  inventory: overviewValues[7][1],
};
for (const key of Object.keys(expected)) {
  if (actual[key] !== expected[key]) errors.push(`Overview ${key}: expected ${expected[key]}, got ${actual[key]}`);
}

const people = workbook.worksheets.getItem("Consolidated People").getUsedRange().values;
const families = workbook.worksheets.getItem("Consolidated Families").getUsedRange().values;
const chrisRow = people.find((row) => row[0] === "I335");
const chrisFamilyRow = families.find((row) => row[1] === "I176" && row[2] === "I334" && String(row[3]).split(";").includes("I335"));
const williamRow = people.find((row) => row[0] === "I336");
const williamParentsRow = families.find((row) => row[1] === "I338" && row[2] === "I339" && String(row[3]).split(";").includes("I336"));
const nilsRow = people.find((row) => row[0] === "I344");
const nilsMotherOnlyRow = families.find((row) => !row[1] && row[2] === "I346" && String(row[3]).split(";").includes("I344"));
const aliceRow = people.find((row) => row[0] === "I337");
if (!chrisRow || !String(chrisRow[7]).includes("paternal half-brother")) {
  errors.push("Chris person row does not record the owner-confirmed paternal half-brother relationship");
}
if (!chrisFamilyRow) {
  errors.push("No consolidated family row links Henry I176 and Mary Alice I334 as Chris I335's parents");
}
if (!williamRow || williamRow[1] !== "William John Thoren" || !williamParentsRow) {
  errors.push("William John Thoren or the Christian I338–Augusta I339 parent link is missing");
}
if (!nilsRow || !nilsMotherOnlyRow || !String(nilsRow[7]).includes("father remains blank")) {
  errors.push("Nils Svensson's mother-only parent record or blank-father safeguard is missing");
}
if (!aliceRow || String(aliceRow[8] ?? "")) {
  errors.push("Alice Gallaher has an imported parent family despite unresolved parentage");
}

console.log(JSON.stringify({
  sheets,
  overview: actual,
  chrisRelationship: {
    person: chrisRow?.[1] ?? null,
    fatherId: chrisFamilyRow?.[1] ?? null,
    motherId: chrisFamilyRow?.[2] ?? null,
    childId: chrisFamilyRow?.[3] ?? null,
  },
  maryAliceAncestry: {
    william: williamRow?.[1] ?? null,
    williamFatherId: williamParentsRow?.[1] ?? null,
    williamMotherId: williamParentsRow?.[2] ?? null,
    nilsNamedFatherId: nilsMotherOnlyRow?.[1] ?? null,
    nilsMotherId: nilsMotherOnlyRow?.[2] ?? null,
    aliceParentFamilyId: aliceRow?.[8] ?? null,
  },
  formulaErrors: errors,
}, null, 2));
if (errors.length) process.exitCode = 1;
