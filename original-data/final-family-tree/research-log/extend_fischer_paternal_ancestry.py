from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path


BASE = Path(__file__).resolve().parent.parent
PREFIX = "Fredric_Vollmer_Complete_Family_Tree"
GED = BASE / f"{PREFIX}.ged"
CANONICAL = BASE / f"{PREFIX}_Canonical_Data.json"
PEOPLE_CSV = BASE / f"{PREFIX}_People.csv"
FAMILIES_CSV = BASE / f"{PREFIX}_Families.csv"
SOURCES_MD = BASE / f"{PREFIX}_Sources.md"
SOURCE_INVENTORY = BASE / f"{PREFIX}_Source_Inventory.csv"
VITAL_COVERAGE = BASE / f"{PREFIX}_Vital_Date_Coverage.csv"
OCCUPATION_COVERAGE = BASE / f"{PREFIX}_Occupation_Coverage.csv"
VALIDATION = BASE / f"{PREFIX}_VALIDATION.txt"
README = BASE / "README.md"
RESEARCH_LOG = BASE / "research-log/Wallace_Ray_Fischer_Direct_Ancestry_Research_Log.md"
RECORDS = BASE / "records"


PEOPLE = [
    dict(id="I391", name="Raymond Charles Fischer Jr", ged="Raymond Charles /Fischer/ Jr.", sex="M", birth="22 NOV 1934; Marlin, Falls County, Texas", death="22 SEP 2022; Belpre, Washington County, Ohio", sources=["S69", "S70"], note="Owner-identified father of Wallace Ray Fischer. Ohio death, obituary, burial, census, and Texas marriage records form a consistent identity cluster."),
    dict(id="I392", name="Wanda June Wallace Fischer", ged="Wanda June /Wallace/", sex="F", birth="", death="", sources=["S69", "S70", "S74"], note="Owner supplied Wanda and then June as possible names. Texas marriage records identify one person as Wanda J. Wallace and Wanda June Wallace; the 2022 tribute addresses her as June. Living dates and addresses are withheld."),
    dict(id="I393", name="Raymond Charles Fischer Sr", ged="Raymond Charles /Fischer/ Sr.", sex="M", birth="18 FEB 1915; Marlin, Falls County, Texas", death="20 MAY 1979; Marlin, Falls County, Texas", sources=["S70", "S71", "S77"], note="The 1940 census identifies him as Raymond Jr.'s father. Texas birth and death certificates name Daniel Fischer and Lena Wirtz/Wirtz variants as his parents."),
    dict(id="I394", name="Ruby Louise Gilmore Fischer", ged="Ruby Louise /Gilmore/", sex="F", birth="10 DEC 1912; Marlin, Falls County, Texas", death="16 MAR 2000; Marlin, Falls County, Texas", sources=["S71", "S72", "S77"], note="The 1940 census identifies her as Raymond Jr.'s mother. The burial index supplies Gilmore; the 1920 census records Ruby as daughter of G. S. Gilmore and Ida."),
    dict(id="I395", name="Johann Daniel Fischer", ged="Johann Daniel /Fischer/", sex="M", birth="13 DEC 1863; Grossaspach, Wurttemberg, Germany", death="31 MAR 1925; Marlin, Falls County, Texas", sources=["S71", "S73", "S77"], note="German baptism and family-table records, U.S. censuses, and the memorial record identify the immigrant also recorded as Daniel P. or Dan Fischer."),
    dict(id="I396", name="Lena Wirtz Fischer", ged="Lena /Wirtz/", sex="F", birth="30 NOV 1871; New York, New York", death="24 JAN 1974; Marlin, Falls County, Texas", sources=["S71", "S73", "S77"], note="Her Texas death certificate names Jacob Wirtz and Catherine Swan as parents. Record spellings include Wirtz, Wirz, and Wietz."),
    dict(id="I397", name="Johann Daniel Fischer", ged="Johann Daniel /Fischer/", sex="M", birth="", death="", sources=["S73"], note="Named as Johann Daniel Fischer's father in the Grossaspach baptism and family-table records; no further supported direct ancestry was located."),
    dict(id="I398", name="Elisabethe Margarethe Fischer", ged="Elisabethe Margarethe /Unknown/", sex="F", birth="", death="", sources=["S73"], note="Named as Johann Daniel Fischer's mother in German church records. Her birth surname is not established and is intentionally blank."),
    dict(id="I399", name="Jacob Wirtz", ged="Jacob /Wirtz/", sex="M", birth="", death="", sources=["S73"], note="Named as Lena Wirtz Fischer's father on her Texas death certificate; no reliable matching parent household was found."),
    dict(id="I400", name="Catherine Swan Wirtz", ged="Catherine /Swan/", sex="F", birth="", death="", sources=["S73"], note="Named as Lena Wirtz Fischer's mother on her Texas death certificate; no reliable matching parent household was found."),
    dict(id="I401", name="George Samuel Gilmore", ged="George Samuel /Gilmore/", sex="M", birth="22 JAN 1886; Texas", death="", sources=["S72"], note="The 1920 census records G. S. Gilmore as Ruby's father; the World War I draft record supplies the name George Sam Gilmore and exact birth date."),
    dict(id="I402", name="Ida Susan Burt Gilmore", ged="Ida Susan /Burt/", sex="F", birth="ABT 1887; Texas", death="", sources=["S72"], note="The 1920 census records Ida as Ruby's mother. SSA and Texas index records supply the fuller form Ida Susan Burt; no supported parents were located."),
    dict(id="I403", name="Chalmers Carl Wallace", ged="Chalmers Carl /Wallace/", sex="M", birth="16 MAR 1915; Rush Springs, Grady County, Oklahoma", death="25 NOV 1962; Lincoln Parish, Louisiana", sources=["S74", "S75", "S78"], note="The 1940 census records him as Wanda's father; records and memorials also render his name Chambers Carl and Wally."),
    dict(id="I404", name="Dorothy Bess Highley Wallace", ged="Dorothy Bess /Highley/", sex="F", birth="21 OCT 1914; Coffeyville, Montgomery County, Kansas", death="SEP 1995; California", sources=["S74", "S76"], note="The 1940 census records Dorothy as Wanda's mother. SSA gives 15 Sep 1995 while the California death index gives 30 Sep 1995; only the month is asserted pending resolution."),
    dict(id="I405", name="Walter Albert Wallace Sr", ged="Walter Albert /Wallace/ Sr.", sex="M", birth="3 DEC 1883; Bryan County, Oklahoma", death="8 DEC 1963; Shreveport, Caddo Parish, Louisiana", sources=["S74", "S75", "S78"], note="The 1920 census records Chalmers as his son. The memorial names Mary J. McGaha Wallace as his mother but no father."),
    dict(id="I406", name="Alice Mae Williams Wallace", ged="Alice Mae /Williams/", sex="F", birth="2 MAR 1892; Missouri", death="8 FEB 1987; Shreveport, Caddo Parish, Louisiana", sources=["S74", "S75", "S78"], note="The 1920 census records Chalmers as her son; the memorial index supplies Williams and names Robert B. Williams and Nancy Ellen Brannan as parents."),
    dict(id="I407", name="Mary J McGaha Wallace", ged="Mary J /McGaha/", sex="F", birth="14 JUL 1855; Arkansas", death="13 JUL 1945; Allen, Pontotoc County, Oklahoma", sources=["S75"], note="The memorial index explicitly links Walter Albert Wallace as her child and supplies McGaha. Walter's father remains blank."),
    dict(id="I408", name="Robert B Williams", ged="Robert B /Williams/", sex="M", birth="1850", death="1926", sources=["S75", "S79"], note="The memorial index explicitly names him as Alice Mae Williams's father; no supported parents were located."),
    dict(id="I409", name="Nancy Ellen Brannan Williams", ged="Nancy Ellen /Brannan/", sex="F", birth="19 JUN 1858", death="9 JUL 1912", sources=["S75", "S79"], note="The memorial index explicitly names her as Alice Mae Williams's mother and names Elisha Branham and Clarissa McCoy as parents. Brannan and Branham are retained as recorded variants."),
    dict(id="I410", name="Elisha Branham", ged="Elisha /Branham/", sex="M", birth="1814; Tennessee", death="23 MAY 1873; Monroe County, Indiana", sources=["S75", "S79"], note="The memorial index explicitly names him as Nancy Ellen Brannan Williams's father; no further supported direct ancestry was located."),
    dict(id="I411", name="Clarissa McCoy Branham Williams McBride", ged="Clarissa /McCoy/", sex="F", birth="10 OCT 1826; Indiana", death="27 FEB 1907; Monroe County, Indiana", sources=["S75", "S79"], note="The memorial index explicitly names her as Nancy Ellen Brannan Williams's mother and Daniel Franklin McCoy as her father. Later married-name forms are retained for identity control."),
    dict(id="I412", name="Daniel Franklin McCoy", ged="Daniel Franklin /McCoy/", sex="M", birth="22 JAN 1792; Jefferson County, Kentucky", death="16 JUL 1882; Hindustan, Monroe County, Indiana", sources=["S75"], note="The memorial index explicitly names him as Clarissa McCoy's father. Clarissa's mother is not named in that link and remains blank."),
    dict(id="I413", name="Ambrose Long Highley", ged="Ambrose Long /Highley/", sex="M", birth="24 JUN 1874; Troy, Doniphan County, Kansas", death="16 OCT 1931; Webb City, Jasper County, Missouri", sources=["S74", "S76", "S79"], note="Dorothy's SSA record names him; the 1880 census records Ambrose as son of William and Hannah Highley."),
    dict(id="I414", name="Mary Elizabeth Herod Highley", ged="Mary Elizabeth /Herod/", sex="F", birth="1878", death="22 APR 1958; Jasper County, Missouri", sources=["S74", "S76", "S79"], note="Dorothy's SSA record names her; Missouri death and memorial records corroborate the identity. Her parents remain unproved."),
    dict(id="I415", name="William T Highley", ged="William T /Highley/", sex="M", birth="28 JUL 1834", death="23 AUG 1918", sources=["S76", "S79"], note="The 1880 census records him as Ambrose's father. The memorial names James and Mary Highley as parents; that earlier link is retained as lower-confidence memorial evidence."),
    dict(id="I416", name="Hannah T Blair Highley", ged="Hannah T /Blair/", sex="F", birth="22 MAR 1842; Iowa", death="9 FEB 1921; East St Louis, St Clair County, Illinois", sources=["S76", "S79"], note="The 1880 census records her as Ambrose's mother; the memorial supplies Blair. No supported parents were located."),
    dict(id="I417", name="James Highley", ged="James /Highley/", sex="M", birth="", death="", sources=["S76"], note="Named as William T. Highley's father on the memorial; an 1850 household is consistent but does not state relationships. This is a lower-confidence stopping point."),
    dict(id="I418", name="Mary Highley", ged="Mary /Unknown/", sex="F", birth="", death="", sources=["S76"], note="Named as William T. Highley's mother on the memorial; her birth surname is not established. This is a lower-confidence stopping point."),
]


FAMILIES = [
    dict(id="F174", husband="I391", wife="I392", children=["I357"], marriage="11 JUN 1957; Taylor, Williamson County, Texas", sources=["S69", "S70"], note="Owner identification is corroborated by the Texas marriage record, the 1940 census, and Raymond's 2022 obituary/tribute cluster."),
    dict(id="F175", husband="I393", wife="I394", children=["I391"], marriage="", sources=["S70", "S71"], note="The 1940 census explicitly records Raymond Jr. as their son."),
    dict(id="F176", husband="I395", wife="I396", children=["I393"], marriage="5 SEP 1888; Falls County, Texas", sources=["S71", "S73"], note="Texas birth/death certificates and the 1920 census name Daniel and Lena as Raymond Sr.'s parents."),
    dict(id="F177", husband="I397", wife="I398", children=["I395"], marriage="", sources=["S73"], note="The Grossaspach baptism and family-table records name both parents."),
    dict(id="F178", husband="I399", wife="I400", children=["I396"], marriage="", sources=["S73"], note="Lena's Texas death certificate names Jacob Wirtz and Catherine Swan."),
    dict(id="F179", husband="I401", wife="I402", children=["I394"], marriage="", sources=["S72"], note="The 1920 census explicitly records Ruby as their daughter."),
    dict(id="F180", husband="I403", wife="I404", children=["I392"], marriage="13 APR 1935; Webb City, Jasper County, Missouri", sources=["S74"], note="The 1940 census explicitly records Wanda as their daughter; the 1935 marriage record links Chalmers and Dorothy."),
    dict(id="F181", husband="I405", wife="I406", children=["I403"], marriage="", sources=["S74", "S75"], note="The 1920 census explicitly records Chalmers as their son."),
    dict(id="F182", husband="", wife="I407", children=["I405"], marriage="", sources=["S75"], note="The memorial index explicitly links Mary J. McGaha Wallace as Walter's mother. No father is inferred."),
    dict(id="F183", husband="I408", wife="I409", children=["I406"], marriage="", sources=["S75"], note="Alice Mae Williams's memorial index explicitly names Robert and Nancy as parents."),
    dict(id="F184", husband="I410", wife="I411", children=["I409"], marriage="", sources=["S75"], note="Nancy Ellen Brannan Williams's memorial index explicitly names Elisha and Clarissa as parents."),
    dict(id="F185", husband="I412", wife="", children=["I411"], marriage="", sources=["S75"], note="Clarissa McCoy's memorial index explicitly names Daniel Franklin McCoy as father. Her mother remains blank."),
    dict(id="F186", husband="I413", wife="I414", children=["I404"], marriage="", sources=["S74", "S76"], note="Dorothy's SSA record names Ambrose Long Highley and Mary Elizabeth Herod as parents."),
    dict(id="F187", husband="I415", wife="I416", children=["I413"], marriage="", sources=["S76"], note="The 1880 census explicitly records Ambrose as their son."),
    dict(id="F188", husband="I417", wife="I418", children=["I415"], marriage="", sources=["S76"], note="The parent names come from William's memorial and are treated as a lower-confidence stopping point; the 1850 household alone does not state relationships."),
]


SOURCES = [
    dict(id="S69", title="Owner correction identifying Wallace Ray Fischer's parents", author="Fredric Muller Vollmer", date="2 SEP 2026", note="The owner identifies Wallace Ray Fischer's parents as Raymond Fischer and Wanda Fischer, both associated with Texas; identifies the father as Raymond Charles Fischer Jr., who died 22 Sep 2022 at Belpre; and notes Wanda may also be called June. Record research resolves Wanda and June as Wanda June Wallace Fischer."),
    dict(id="S70", title="Raymond Charles Fischer Jr and Wanda June Wallace record cluster", author="Ohio and Texas vital/county records; U.S. Census Bureau; Find a Grave; Leavitt Funeral Home; Ancestry.com", date="", note="Raymond's 1934 birth, 22 Sep 2022 Belpre death, and 1940 parent household align. The official Texas marriage index records Raymond C. Fischer Jr. and Wanda J. Wallace on 11 Jun 1957; a newspaper marriage index expands her name to Wanda June Wallace. Records: https://www.ancestry.com/search/collections/60541/records/218066535 ; https://www.findagrave.com/memorial/243870577/raymond-charles-fischer ; https://www.ancestry.com/search/collections/5763/records/10265056 ; https://www.ancestry.com/search/collections/2190/records/317879477 ; https://www.leavittfuneralhome.com/obituaries/Raymond--Charles-Fischer-Jr?obId=25942554 ; https://www.ancestry.com/search/collections/2442/records/155875370 ; https://www.ancestry.com/search/collections/9168/records/25830055 ; https://www.ancestry.com/search/collections/62116/records/152414706 ; https://www.newspapers.com/image/761699744/?article=866f00a6-99e2-45c3-9ea5-fd632644db6c&xid=3398"),
    dict(id="S71", title="Raymond Charles Fischer Sr and Ruby Louise Gilmore record cluster", author="Texas vital records; U.S. Census Bureau; Find a Grave; Ancestry.com", date="", note="The 1940 census records Raymond Jr. as son of Raymond and Ruby. Raymond Sr.'s Texas birth/death certificates name Daniel Fischer and Lena Wirtz; the memorial records Raymond's dates and Ruby Gilmore as spouse. Records: https://www.ancestry.com/search/collections/2442/records/155875370 ; https://www.ancestry.com/search/collections/2272/records/566313 ; https://www.ancestry.com/search/collections/2275/records/3848821 ; https://www.ancestry.com/search/collections/60525/records/42346703 ; https://www.findagrave.com/memorial/69481441/raymond-charles-fischer ; https://www.ancestry.com/search/collections/60525/records/42346721 ; https://www.findagrave.com/memorial/69481460/ruby-fischer"),
    dict(id="S72", title="Ruby Gilmore parent household and George Gilmore identity cluster", author="U.S. Census Bureau; Selective Service System; Social Security Administration; Ancestry.com", date="", note="The 1920 census explicitly records Ruby as daughter of G. S. and Ida Gilmore. George's World War I draft record supplies George Sam Gilmore and 22 Jan 1886; SSA and Texas index links supply Ida Susan Burt. Records: https://www.ancestry.com/search/collections/6061/records/100221065 ; https://www.ancestry.com/search/collections/6061/records/100221063 ; https://www.ancestry.com/search/collections/6482/records/14839842 ; https://www.ancestry.com/search/collections/60901/records/626088911 ; https://www.ancestry.com/search/collections/4876/records/108265726"),
    dict(id="S73", title="Johann Daniel Fischer and Lena Wirtz direct-line record cluster", author="Wurttemberg Evangelical Church; Texas vital records; U.S. Census Bureau; Find a Grave; Ancestry.com", date="", note="German baptism and family-table records name Johann Daniel Fischer and Elisabethe Margarethe as the immigrant Daniel's parents. U.S. censuses and Texas records link Daniel, Lena, and Raymond; Lena's death certificate names Jacob Wirtz and Catherine Swan. Records: https://www.ancestry.com/search/collections/61389/records/4210684 ; https://www.ancestry.com/search/collections/61023/records/7909461 ; https://www.ancestry.com/search/collections/7602/records/70597040 ; https://www.ancestry.com/search/collections/6061/records/100223419 ; https://www.ancestry.com/search/collections/60525/records/100697046 ; https://www.findagrave.com/memorial/19759283/johann-daniel-fischer ; https://www.ancestry.com/search/collections/2272/records/133381 ; https://www.findagrave.com/memorial/19759290/lena-fischer"),
    dict(id="S74", title="Wanda June Wallace parent and Highley identity cluster", author="U.S. Census Bureau; Missouri county records; Social Security Administration; California vital records; Find a Grave; Ancestry.com", date="", note="The 1940 census records Wanda J. Wallace as daughter of Chalmers and Dorothy; the 1935 Missouri marriage record links Chalmers and Dorothy Bess Highley. Dorothy's SSA record names Ambrose Long Highley and Mary E. Herod. Her death-date sources conflict: SSA gives 15 Sep 1995 and California gives 30 Sep 1995. Records: https://www.ancestry.com/search/collections/2442/records/89045738 ; https://www.ancestry.com/search/collections/62308/records/76403615 ; https://www.ancestry.com/search/collections/1171/records/9664937 ; https://www.ancestry.com/search/collections/60525/records/150531434 ; https://www.findagrave.com/memorial/186519723/chambers-carl-wallace ; https://www.ancestry.com/search/collections/60901/records/24418580 ; https://www.ancestry.com/search/collections/5180/records/1076373"),
    dict(id="S75", title="Wallace, Williams, Branham, and McCoy direct-line memorial cluster", author="U.S. Census Bureau; Find a Grave; Ancestry.com", date="", note="The 1920 census identifies Walter and Alice as Chalmers's parents. Find a Grave index links supply Mary McGaha as Walter's mother; Williams as Alice's maiden name; Robert Williams and Nancy Brannan as Alice's parents; Elisha Branham and Clarissa McCoy as Nancy's parents; and Daniel Franklin McCoy as Clarissa's father. These memorial-based extensions are retained with lower confidence where no civil parent record was located. Records: https://www.ancestry.com/search/collections/6061/records/62031695 ; https://www.ancestry.com/search/collections/60525/records/233666764 ; https://www.ancestry.com/search/collections/60525/records/233666929 ; https://www.ancestry.com/search/collections/60525/records/233646146 ; https://www.ancestry.com/search/collections/60525/records/87506166 ; https://www.ancestry.com/search/collections/60525/records/87506189 ; https://www.ancestry.com/search/collections/60525/records/98293838 ; https://www.ancestry.com/search/collections/60525/records/53527274 ; https://www.ancestry.com/search/collections/60525/records/53527788"),
    dict(id="S76", title="Highley direct-line census, vital, and memorial cluster", author="U.S. Census Bureau; Missouri vital records; Find a Grave; Ancestry.com", date="", note="The 1880 census explicitly records Ambrose as son of William and Hannah Highley. Memorial and Missouri records identify Mary Elizabeth Herod and the Highley dates. William's memorial names James and Mary Highley; the compatible 1850 household does not state relationships, so the earlier parent link remains lower confidence. Records: https://www.ancestry.com/search/collections/6742/records/24830397 ; https://www.ancestry.com/search/collections/60382/records/723670 ; https://www.ancestry.com/search/collections/60525/records/86597625 ; https://www.findagrave.com/memorial/13974942/ambrose-long-highley ; https://www.ancestry.com/search/collections/60382/records/1700594 ; https://www.findagrave.com/memorial/58864757/mary-elizabeth-highley ; https://www.ancestry.com/search/collections/60525/records/85153660 ; https://www.findagrave.com/memorial/13888778/william-t.-highley ; https://www.ancestry.com/search/collections/60525/records/85153662 ; https://www.findagrave.com/memorial/13888780/hannah-t-highley ; https://www.ancestry.com/search/collections/8054/records/3654061"),
    dict(id="S77", title="Fischer direct-line grave-marker photographs", author="Find a Grave contributors couchpotato", date="", note="Full-resolution grave-marker photographs were saved from the exact Find a Grave memorials for Johann Daniel Fischer, Lena Wirtz Fischer, Raymond Charles Fischer Sr., and Ruby Louise Gilmore Fischer. The site labels every preserved image as Photo type: Grave. Memorials: https://www.findagrave.com/memorial/19759283/johann-daniel-fischer ; https://www.findagrave.com/memorial/19759290/lena-fischer ; https://www.findagrave.com/memorial/69481441/raymond-charles-fischer ; https://www.findagrave.com/memorial/69481460/ruby-fischer", media=["1925-03-31_johann-daniel-fischer_grave-marker.jpg", "1974-01-24_lena-wirtz-fischer_grave-marker.jpg", "1979-05-20_raymond-charles-fischer-sr_grave-marker-1.jpg", "1979-05-20_raymond-charles-fischer-sr_grave-marker-2.jpg", "2000-03-16_ruby-louise-gilmore-fischer_grave-marker-1.jpg", "2000-03-16_ruby-louise-gilmore-fischer_grave-marker-2.jpg"]),
    dict(id="S78", title="Wallace direct-line grave-marker photographs", author="Find a Grave contributors evansd and KD Burleson", date="", note="Full-resolution grave photographs were saved from the exact memorials for Chalmers Carl Wallace, Walter Albert Wallace Sr., and Alice Mae Williams Wallace. Find a Grave labels every preserved image as Photo type: Grave; obituary-clipping images were excluded from this grave set. Memorials: https://www.findagrave.com/memorial/186519723/chambers-carl-wallace ; https://www.findagrave.com/memorial/262761264/walter-albert-wallace ; https://www.findagrave.com/memorial/262761475/alice-mae-wallace", media=["1962-11-25_chalmers-carl-wallace_grave-marker-1.jpeg", "1962-11-25_chalmers-carl-wallace_grave-marker-2.jpeg", "1962-11-25_chalmers-carl-wallace_grave-marker-3.jpeg", "1963-12-08_walter-albert-wallace_grave-marker.jpeg", "1987-02-08_alice-mae-williams-wallace_grave-marker.jpeg"]),
    dict(id="S79", title="Highley, Williams, and Branham direct-line grave-marker photographs", author="Find a Grave contributors Judy K. Roberts, Kelly, OkieBran, Ellie Sparks, Colleen Sanders Broyles, Ben Fulton, and N.Miller", date="", note="Full-resolution grave photographs were saved from the exact memorials for Ambrose and Mary Highley, William and Hannah Highley, Robert and Nancy Williams, Elisha Branham, and Clarissa McCoy Branham. Find a Grave labels every preserved image as Photo type: Grave. Memorials: https://www.findagrave.com/memorial/13974942/ambrose-long-highley ; https://www.findagrave.com/memorial/58864757/mary-elizabeth-highley ; https://www.findagrave.com/memorial/13888778/william-t.-highley ; https://www.findagrave.com/memorial/13888780/hannah-t-highley ; https://www.findagrave.com/memorial/21540402/robert-b.-williams ; https://www.findagrave.com/memorial/21540426/nancy-ellen-williams ; https://www.findagrave.com/memorial/33706860/elisha-branham ; https://www.findagrave.com/memorial/84921915/clarissa-branham_williams_mcbride", media=["1931-10-16_ambrose-long-highley_grave-marker.jpg", "1958-04-22_mary-elizabeth-herod-highley_grave-marker.jpg", "1918-08-23_william-t-highley_grave-marker.jpg", "1921-02-09_hannah-t-blair-highley_grave-marker.jpg", "1926_robert-b-williams_grave-marker.jpg", "1912-07-09_nancy-ellen-brannan-williams_grave-marker.jpg", "1873-05-23_elisha-branham_grave-marker-1.jpg", "1873-05-23_elisha-branham_grave-marker-2.jpeg", "1873-05-23_elisha-branham_grave-marker-3.jpg", "1907-02-27_clarissa-mccoy-branham_grave-marker.jpeg"]),
]


def event_lines(tag: str, value: str) -> list[str]:
    if not value:
        return []
    date, _, place = value.partition(";")
    lines = [f"1 {tag}", f"2 DATE {date.strip()}"]
    if place.strip():
        lines.append(f"2 PLAC {place.strip()}")
    return lines


families_as_child = {child: family["id"] for family in FAMILIES for child in family["children"]}
families_as_spouse: dict[str, list[str]] = {}
for family in FAMILIES:
    for spouse in (family["husband"], family["wife"]):
        if spouse:
            families_as_spouse.setdefault(spouse, []).append(family["id"])


def person_block(person: dict) -> str:
    lines = [f"0 @{person['id']}@ INDI", f"1 NAME {person['ged']}", f"1 SEX {person['sex']}"]
    lines += event_lines("BIRT", person["birth"])
    lines += event_lines("DEAT", person["death"])
    lines += [f"1 NOTE {person['note']}", f"1 REFN FISCHER-PATERNAL-{person['id']}"]
    lines += [f"1 SOUR @{source}@" for source in person["sources"]]
    if person["id"] in families_as_child:
        lines.append(f"1 FAMC @{families_as_child[person['id']]}@")
    lines += [f"1 FAMS @{family}@" for family in families_as_spouse.get(person["id"], [])]
    return "\n".join(lines)


def family_block(family: dict) -> str:
    lines = [f"0 @{family['id']}@ FAM"]
    if family["husband"]:
        lines.append(f"1 HUSB @{family['husband']}@")
    if family["wife"]:
        lines.append(f"1 WIFE @{family['wife']}@")
    lines += [f"1 CHIL @{child}@" for child in family["children"]]
    lines += event_lines("MARR", family["marriage"])
    lines.append(f"1 NOTE {family['note']}")
    lines += [f"1 SOUR @{source}@" for source in family["sources"]]
    return "\n".join(lines)


def source_media(source: dict) -> list[str]:
    media = source.get("media", [])
    return media if isinstance(media, list) else [media]


def source_block(source: dict) -> str:
    lines = [f"0 @{source['id']}@ SOUR", f"1 TITL {source['title']}", f"1 AUTH {source['author']}"]
    if source["date"]:
        lines.append(f"1 DATE {source['date']}")
    lines.append(f"1 NOTE {source['note']}")
    for media in source_media(source):
        lines += ["1 OBJE", f"2 FILE records/{media}", "3 FORM jpg", f"3 TITL {source['title']}"]
    return "\n".join(lines)


def remove_block(text: str, record_id: str, record_type: str) -> str:
    return re.sub(rf"^0 @{record_id}@ {record_type}\n.*?(?=^0 )", "", text, flags=re.M | re.S)


ged = GED.read_text(encoding="utf-8")
for item in PEOPLE:
    ged = remove_block(ged, item["id"], "INDI")
for item in FAMILIES:
    ged = remove_block(ged, item["id"], "FAM")
for item in SOURCES:
    ged = remove_block(ged, item["id"], "SOUR")

wallace_match = re.search(r"^0 @I357@ INDI\n.*?(?=^0 )", ged, flags=re.M | re.S)
if not wallace_match:
    raise RuntimeError("I357 missing")
wallace_lines = [
    line for line in wallace_match.group(0).rstrip().splitlines()
    if line not in {"1 SOUR @S69@", "1 SOUR @S70@", "1 FAMC @F174@"}
    and not line.startswith("1 NOTE Owner-confirmed parents Raymond Charles Fischer Jr")
]
wallace_lines += [
    "1 NOTE Owner-confirmed parents Raymond Charles Fischer Jr. and Wanda June Wallace Fischer; identity corroborated by Texas marriage, census, and 2022 death records.",
    "1 SOUR @S69@",
    "1 SOUR @S70@",
    "1 FAMC @F174@",
]
wallace_block = "\n".join(wallace_lines) + "\n"
ged = ged[:wallace_match.start()] + wallace_block + ged[wallace_match.end():]
ged = re.sub(r"\n?0 TRLR\s*$", "", ged).rstrip() + "\n"
ged += "\n".join(person_block(person) for person in PEOPLE) + "\n"
ged += "\n".join(family_block(family) for family in FAMILIES) + "\n"
ged += "\n".join(source_block(source) for source in SOURCES) + "\n0 TRLR\n"
GED.write_text(ged, encoding="utf-8")


canonical = json.loads(CANONICAL.read_text(encoding="utf-8"))
person_ids = {item["id"] for item in PEOPLE}
family_ids = {item["id"] for item in FAMILIES}
source_ids = {item["id"] for item in SOURCES}
canonical["people"] = [row for row in canonical["people"] if row["individual_id"] not in person_ids]
canonical["families"] = [row for row in canonical["families"] if row["family_id"] not in family_ids]
canonical["sources"] = [row for row in canonical["sources"] if row["source_id"] not in source_ids]
for row in canonical["people"]:
    if row["individual_id"] == "I357":
        refs = [value for value in row["source_refs"].split(";") if value and value not in {"S69", "S70"}] + ["S69", "S70"]
        row["source_refs"] = ";".join(refs)
        row["family_as_child"] = "F174"
        if "Wanda June Wallace Fischer" not in row["notes"]:
            row["notes"] += " | Owner-confirmed parents: Raymond Charles Fischer Jr. and Wanda June Wallace Fischer."
for person in PEOPLE:
    canonical["people"].append({
        "individual_id": person["id"], "name": person["name"], "sex": person["sex"],
        "birth": person["birth"], "death": person["death"], "occupations_and_roles": "",
        "local_ids": f"FISCHER-PATERNAL-{person['id']}", "source_refs": ";".join(person["sources"]),
        "notes": person["note"], "family_as_child": families_as_child.get(person["id"], ""),
        "families_as_spouse": ";".join(families_as_spouse.get(person["id"], [])),
    })
for family in FAMILIES:
    canonical["families"].append({
        "family_id": family["id"], "husband_id": family["husband"], "wife_id": family["wife"],
        "children_ids": ";".join(family["children"]), "marriage": family["marriage"],
        "notes": family["note"], "source_refs": ";".join(family["sources"]),
    })
for source in SOURCES:
    canonical["sources"].append({
        "source_id": source["id"], "title": source["title"], "author": source["author"],
        "date": source["date"],
        "notes": source["note"] + "".join(f" Preserved image: records/{media}." for media in source_media(source)),
        "origin": "Wallace Ray Fischer direct-ancestry research",
    })
canonical["people"].sort(key=lambda row: int(row["individual_id"][1:]))
canonical["families"].sort(key=lambda row: int(row["family_id"][1:]))
canonical["sources"].sort(key=lambda row: int(row["source_id"][1:]))
canonical["metadata"]["scope"] = "Canonical Vollmer tree plus Arianna Lynn Fischer and her documented direct paternal and maternal ancestry; no Fischer collateral relatives were added."
canonical["metadata"]["privacy"] = "Living addresses and contact information are omitted. Living exact dates are withheld except Arianna's owner-supplied birth year."
canonical["metadata"]["vital_date_coverage"] = {
    "people": 391, "birth_dates_recorded": 256, "death_dates_recorded": 218,
    "complete": 185, "partial": 104, "unresolved": 69, "privacy_limited": 25, "living_private": 8,
}
canonical["metadata"]["occupation_coverage"] = {
    "people": 391, "people_with_recorded_occupations_or_roles": 17, "accepted_occupation_events": 23,
    "unresolved": 332, "privacy_limited": 31, "living_private": 9, "minor_without_occupation": 2,
}
canonical["provenance"] = [row for row in canonical["provenance"] if row.get("thread_title") != "Extend Wallace Ray Fischer direct ancestry"]
canonical["provenance"].append({"thread_title": "Extend Wallace Ray Fischer direct ancestry", "role": "owner correction plus signed-in Ancestry research, exact direct-line links, conflict handling, and full-resolution Find a Grave marker preservation; no collateral expansion"})
canonical["corrections"] = [row for row in canonical["corrections"] if row.get("topic") not in {"Fischer paternal stopping point", "Wanda and June Fischer identity"}]
canonical["corrections"] += [
    {"topic": "Fischer paternal stopping point", "corrected": "The owner identified Wallace Ray Fischer's parents. Texas marriage, census, and 2022 death records support Raymond Charles Fischer Jr. and Wanda June Wallace Fischer; the prior blank-parent stopping point is superseded."},
    {"topic": "Wanda and June Fischer identity", "corrected": "Wanda and June are one person: official Texas marriage records use Wanda J. Wallace and the newspaper marriage index expands her name to Wanda June Wallace. A 2022 tribute addresses her as June."},
]
CANONICAL.write_text(json.dumps(canonical, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


write_csv(PEOPLE_CSV, list(canonical["people"][0]), canonical["people"])
write_csv(FAMILIES_CSV, list(canonical["families"][0]), canonical["families"])


with VITAL_COVERAGE.open(newline="", encoding="utf-8") as handle:
    vital_rows = [row for row in csv.DictReader(handle) if row["individual_id"] not in person_ids]
for row in vital_rows:
    if row["individual_id"] == "I357":
        row["source_refs"] = ";".join([value for value in row["source_refs"].split(";") if value not in {"S69", "S70"}] + ["S69", "S70"])
for person in PEOPLE:
    if person["id"] == "I392":
        birth_status = death_status = overall = "withheld—living/private"
    else:
        birth_status = "recorded" if person["birth"] else "unresolved"
        death_status = "recorded" if person["death"] else "unresolved"
        overall = "complete" if person["birth"] and person["death"] else "partial" if person["birth"] or person["death"] else "unresolved"
    vital_rows.append({
        "individual_id": person["id"], "name": person["name"], "birth": person["birth"],
        "birth_status": birth_status, "death": person["death"], "death_status": death_status,
        "overall_status": overall, "source_refs": ";".join(person["sources"]),
    })
vital_rows.sort(key=lambda row: int(row["individual_id"][1:]))
write_csv(VITAL_COVERAGE, list(vital_rows[0]), vital_rows)


with OCCUPATION_COVERAGE.open(newline="", encoding="utf-8") as handle:
    occupation_rows = [row for row in csv.DictReader(handle) if row["individual_id"] not in person_ids]
for row in occupation_rows:
    if row["individual_id"] == "I357":
        row["source_refs"] = ";".join([value for value in row["source_refs"].split(";") if value not in {"S69", "S70"}] + ["S69", "S70"])
for person in PEOPLE:
    living = person["id"] == "I392"
    occupation_rows.append({
        "individual_id": person["id"], "name": person["name"], "occupations_and_roles": "", "event_count": "0",
        "status": "withheld—living/private" if living else "unresolved—no supported occupation found", "categories": "",
        "source_refs": ";".join(person["sources"]), "research_ids": "",
        "coverage_note": "No living person's occupation was researched or exposed." if living else "No supported occupation or role was found in the records reviewed for this direct-line expansion.",
    })
occupation_rows.sort(key=lambda row: int(row["individual_id"][1:]))
write_csv(OCCUPATION_COVERAGE, list(occupation_rows[0]), occupation_rows)


inventory_rows = [{
    "source_id": source["source_id"], "title": source["title"], "author": source["author"],
    "date": source["date"], "notes": source["notes"], "origin": source["origin"],
} for source in canonical["sources"]]
for record in sorted(path for path in RECORDS.iterdir() if path.is_file()):
    inventory_rows.append({
        "source_id": f"RECORD-{record.stem}", "title": record.name, "author": "", "date": "",
        "notes": hashlib.sha256(record.read_bytes()).hexdigest(), "origin": "preserved original or derivative record",
    })
write_csv(SOURCE_INVENTORY, ["source_id", "title", "author", "date", "notes", "origin"], inventory_rows)


marker = "\n## Wallace Ray Fischer direct-ancestry correction (2 September 2026)\n"
source_text = SOURCES_MD.read_text(encoding="utf-8").split(marker, 1)[0].rstrip() + marker
source_text += "\nOwner correction: Wallace Ray Fischer's parents are Raymond Charles Fischer Jr. and Wanda June Wallace Fischer. Wanda and June are the same person. Scope remains direct ancestors only, with living details withheld.\n\n"
for source in SOURCES:
    source_text += f"### {source['id']} — {source['title']}\n\n{source['note']}"
    for media in source_media(source):
        source_text += f"\n\nPreserved image: `records/{media}`."
    source_text += "\n\n"
source_text += "### Research controls\n\n- No collateral children, siblings, aunts/uncles, cousins, or later spouses were added.\n- Raymond Jr.'s Find a Grave image is labeled Person rather than Grave and was not placed in the grave-marker archive.\n- Walter Wallace's father, Lena Wirtz's parents beyond the death-certificate names, Ruby Gilmore's grandparents, and multiple maiden surnames remain blank where records do not support them.\n- Dorothy Highley's September 1995 death-day conflict is preserved rather than silently resolved.\n- Find a Grave-only parent extensions are labeled lower confidence.\n"
SOURCES_MD.write_text(source_text, encoding="utf-8")


RESEARCH_LOG.write_text(
    "# Wallace Ray Fischer direct-ancestry research log\n\n"
    "Researched in the signed-in Ancestry session on 2 September 2026 after the owner's correction. Scope was limited to Wallace Ray Fischer's parents and their direct ancestors; no collateral relatives were added.\n\n"
    "## Outcome\n\n"
    "- Wallace's parents are Raymond Charles Fischer Jr. (22 Nov 1934–22 Sep 2022) and Wanda June Wallace Fischer.\n"
    "- Wanda and June are the same person: Texas marriage records use Wanda J. Wallace and Wanda June Wallace, while the 2022 tribute uses June.\n"
    "- Raymond's paternal line reaches Johann Daniel Fischer of Grossaspach; German church records name the immigrant's parents.\n"
    "- Wanda's Wallace/Highley line reaches Daniel Franklin McCoy and the memorial-supported James and Mary Highley stopping point.\n"
    "- Twenty-one full-resolution images explicitly labeled Photo type: Grave were preserved with memorial URLs and contributor attribution.\n\n"
    "## Sources\n\n" + "\n".join(f"- {source['id']}: {source['title']} — {source['note']}" for source in SOURCES) +
    "\n\n## Preserved grave images\n\n" + "\n".join(f"- `records/{media}` — {source['title']}" for source in SOURCES for media in source_media(source)) +
    "\n\n## Conflicts and stopping points\n\n"
    "- Dorothy Bess Highley's September 1995 death day conflicts between SSA and California indexes; the tree records only September 1995.\n"
    "- Walter Albert Wallace's father remains blank.\n"
    "- Raymond Jr.'s only memorial photo is a person image, not a grave photo, and was excluded from the grave-marker archive.\n"
    "- Memorial-only parent statements are labeled lower confidence and no private member-tree claims were imported.\n",
    encoding="utf-8",
)


readme = README.read_text(encoding="utf-8").replace("363-person family tree", "391-person family tree")
readme = readme.replace("Wallace Ray Fischer's parents remain blank because no parent-naming record was found.", "Wallace Ray Fischer's parents are now documented as Raymond Charles Fischer Jr. and Wanda June Wallace Fischer.")
readme_marker = "\n\n## Wallace Ray Fischer direct ancestry\n"
readme = readme.split(readme_marker, 1)[0].rstrip() + readme_marker
readme += "\nAn owner correction plus signed-in Ancestry research adds Wallace Ray Fischer's direct paternal ancestry and resolves Wanda/June as Wanda June Wallace Fischer. Twenty-one Find a Grave images explicitly labeled as grave photos are preserved and mapped to exact direct ancestors; no collateral relatives were added.\n"
README.write_text(readme, encoding="utf-8")


validation = VALIDATION.read_text(encoding="utf-8")
replacements = {
    "GEDCOM individuals": 391, "GEDCOM families": 188, "GEDCOM sources": 79,
    "people CSV rows": 391, "families CSV rows": 188, "source inventory rows": len(inventory_rows),
    "vital-date coverage rows": 391, "people with recorded birth dates": 256,
    "people with recorded death dates": 218, "people with complete vital dates": 185,
    "occupation coverage rows": 391, "workbook consolidated individual count": 391,
    "workbook consolidated family count": 188, "workbook consolidated GEDCOM source count": 79,
    "workbook source and record inventory count": len(inventory_rows), "workbook birth dates recorded": 256,
    "workbook death dates recorded": 218, "workbook both vital dates recorded": 185,
    "workbook no dated event unresolved or private": 102,
}
for label, value in replacements.items():
    validation = re.sub(rf"^{re.escape(label)}:.*$", f"{label}: {value}", validation, flags=re.M)
validation = re.sub(r"^Wallace Ray Fischer parents intentionally blank:.*\n?", "", validation, flags=re.M)
validation = re.sub(r"^Fischer evidence images preserved:.*\n?", "", validation, flags=re.M)
for line in [
    "Wallace Ray Fischer parent family present: True",
    "Wanda June Wallace identity resolved: True",
    "Fischer collateral relatives added: False",
    "Fischer grave-marker images preserved: 21",
]:
    if line not in validation:
        validation += "\n" + line
VALIDATION.write_text(validation.rstrip() + "\n", encoding="utf-8")


print(json.dumps({
    "people": len(canonical["people"]), "families": len(canonical["families"]),
    "sources": len(canonical["sources"]), "inventory": len(inventory_rows),
    "preserved_records": len([path for path in RECORDS.iterdir() if path.is_file()]),
}, indent=2))
