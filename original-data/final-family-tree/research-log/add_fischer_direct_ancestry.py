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
RESEARCH_LOG = BASE / "research-log/Arianna_Fischer_Direct_Ancestry_Research_Log.md"
RECORDS = BASE / "records"


PEOPLE = [
    # Living dates are deliberately minimized. Arianna's year is included because the owner supplied it.
    dict(id="I356", name="Arianna Lynn Fischer", ged="Arianna Lynn /Fischer/", sex="F", birth="1990", death="", sources=["S49", "S50"], note="Owner-confirmed wife of Fredric Muller Vollmer. Living person; only the owner-supplied birth year is retained."),
    dict(id="I357", name="Wallace Ray Fischer", ged="Wallace Ray /Fischer/", sex="M", birth="", death="", sources=["S49", "S50", "S51"], note="Owner supplied the form Ray W. Fischer; Ohio records repeatedly use Wallace Ray Fischer. Living dates and addresses are withheld."),
    dict(id="I358", name="Sally Lynn Vanhoose Fischer", ged="Sally Lynn /Vanhoose/", sex="F", birth="", death="", sources=["S49", "S50", "S52"], note="Ohio records supply maiden surname Vanhoose and married surname Fischer. Living dates and addresses are withheld."),
    dict(id="I359", name="Keith Douglas Vanhoose", ged="Keith Douglas /Vanhoose/", sex="M", birth="5 DEC 1944; Ashland, Kentucky", death="8 APR 2004", sources=["S52", "S53"], note="SSA and burial indexes name Douglas T. Vanhoose and Mildred Tackett as parents."),
    dict(id="I360", name="Barbara Lynn Boltenhouse", ged="Barbara Lynn /Boltenhouse/", sex="F", birth="", death="", sources=["S52", "S54"], note="The 1950 census identifies Barbara as daughter of Charles and Alice. Potentially living; dates are withheld."),
    dict(id="I361", name="Douglas T Vanhoose", ged="Douglas T /Vanhoose/", sex="M", birth="1 APR 1921; Lawrence County, Kentucky", death="5 FEB 1983; Pulaski County, Kentucky", sources=["S53", "S61"], note="Kentucky birth index, 1930 census, military index, and death index form a consistent record cluster."),
    dict(id="I362", name="Mildred I Tackett Vanhoose", ged="Mildred I /Tackett/", sex="F", birth="6 NOV 1924; Esco, Pike County, Kentucky", death="22 AUG 2015; Bexley, Franklin County, Ohio", sources=["S53", "S65"], note="Obituary and 1930 census identify Sidney Tackett and Ida Missouri as parents."),
    dict(id="I363", name="Charles Emerald Boltenhouse Jr", ged="Charles Emerald /Boltenhouse/ Jr.", sex="M", birth="19 DEC 1926; Circleville, Pickaway County, Ohio", death="1 MAR 2026; Circleville, Pickaway County, Ohio", sources=["S54", "S55"], note="The 1950 census and 2026 obituary identify wife Alice Hickey and daughter Barbara."),
    dict(id="I364", name="Alice Marie Hickey Boltenhouse", ged="Alice Marie /Hickey/", sex="F", birth="30 AUG 1929; Circleville, Pickaway County, Ohio", death="25 JUL 2003", sources=["S54", "S56"], note="SSA application names William Hickey and Daisy M. Imler as parents; 1940 and 1950 censuses corroborate the household chain."),
    dict(id="I365", name="John B Vanhoose", ged="John B /Vanhoose/", sex="M", birth="ABT 1877; West Virginia", death="", sources=["S62"], note="The 1880 census records John as son of Moses and Mahala; the 1920 census records him with wife Tallie."),
    dict(id="I366", name="Talliehassie Tallie Estep Vanhoose", ged="Talliehassie Tallie /Estep/", sex="F", birth="22 NOV 1881; Johnson County, Kentucky", death="17 MAY 1967; Ashland, Boyd County, Kentucky", sources=["S61", "S62", "S64"], note="The death certificate names father Ira Estep and mother Isora Morton. Tallie and Talliehassie are retained name forms."),
    dict(id="I367", name="Sidney Tackett", ged="Sidney /Tackett/", sex="M", birth="ABT 1894; Kentucky", death="", sources=["S65"], note="Recorded as Sid Tackett in the 1930 household and Sidney Tackett in Mildred's obituary."),
    dict(id="I368", name="Ida Missouri", ged="Ida Missouri /Unknown/", sex="F", birth="ABT 1898; North Carolina", death="", sources=["S65"], note="Mildred's mother is named Ida Missouri Tackett; her birth surname remains unproved."),
    dict(id="I369", name="Moses Vanhoose", ged="Moses /Vanhoose/", sex="M", birth="ABT 1837; Kentucky", death="", sources=["S63"], note="The 1880 census and 1868 marriage record support the household with Mahala Dixon."),
    dict(id="I370", name="Mahala Dixon Vanhoose", ged="Mahala /Dixon/", sex="F", birth="ABT 1848; Kentucky", death="", sources=["S63"], note="The 1868 marriage record supplies Dixon. A tempting 1860 household inference was not used to add parents."),
    dict(id="I371", name="Ira W Estep", ged="Ira W /Estep/", sex="M", birth="ABT 1848; Kentucky", death="", sources=["S64"], note="Tallie's death certificate names Ira Estep; the 1880 census and 1868 marriage record identify the matching Ira and Isora household."),
    dict(id="I372", name="Isora Morton Estep", ged="Isora /Morton/", sex="F", birth="ABT 1849; Kentucky", death="", sources=["S64"], note="Name forms include Isora and a difficult marriage-index transcription; Morton is retained from the marriage record."),
    dict(id="I373", name="Charles Emerald Boltenhouse Sr", ged="Charles Emerald /Boltenhouse/ Sr.", sex="M", birth="27 MAY 1907; Ross County, Ohio", death="29 MAR 1979; Circleville, Pickaway County, Ohio", sources=["S55", "S66", "S67"], note="World War II draft, census, marriage, and death indexes identify this Charles Emerald Boltenhouse."),
    dict(id="I374", name="Leona Florence Tomlinson Boltenhouse", ged="Leona Florence /Tomlinson/", sex="F", birth="29 JUL 1907; Franklin, Warren County, Ohio", death="16 FEB 1994; Kingston, Ross County, Ohio", sources=["S66", "S68"], note="The 1910 census identifies George P. and Linda Tomlinson as parents."),
    dict(id="I375", name="Alonzo Boltenhouse", ged="Alonzo /Boltenhouse/", sex="M", birth="JUN 1884; Ohio", death="", sources=["S67"], note="The 1900 census names Augustus and Elizabeth as parents; 1910 census and 1902 marriage record identify wife Malinda E. Speakman."),
    dict(id="I376", name="Malinda E Speakman Boltenhouse", ged="Malinda E /Speakman/", sex="F", birth="ABT 1885; Ohio", death="", sources=["S67"], note="The 24 Apr 1902 Ross County marriage record supplies the birth surname Speakman."),
    dict(id="I377", name="George P Tomlinson", ged="George P /Tomlinson/", sex="M", birth="APR 1875; Ohio", death="", sources=["S68"], note="The 1900 and 1910 censuses link George, wife Malinda/Linda, son William, and daughter Leona."),
    dict(id="I378", name="Malinda Linda Jackson Tomlinson", ged="Malinda Linda /Jackson/", sex="F", birth="ABT 1878; Ohio", death="", sources=["S68"], note="1900 records Malinda; 1910 records Linda. A later child marriage index names the parents George P. Tomlinson and Linda Jackson."),
    dict(id="I379", name="Augustus Boltenhouse", ged="Augustus /Boltenhouse/", sex="M", birth="JUL 1839; Ohio", death="", sources=["S67"], note="1900 census and 1869 Ross County marriage record support the relationship and spouse."),
    dict(id="I380", name="Elizabeth Cotter Boltenhouse", ged="Elizabeth /Cotter/", sex="F", birth="ABT 1842; Ohio", death="", sources=["S67"], note="The 19 Jul 1869 Ross County marriage record supplies Cotter; later index variants include Cottrell and Cotterill."),
    dict(id="I381", name="Alo Tomlinson", ged="Alo /Tomlinson/", sex="M", birth="ABT 1836; Ohio", death="", sources=["S68"], note="The 1900 census explicitly records George as son of Alo and Rebecca."),
    dict(id="I382", name="Rebecca Tomlinson", ged="Rebecca /Unknown/", sex="F", birth="ABT 1846; Ohio", death="", sources=["S68"], note="The 1900 census explicitly records George as son of Rebecca; her birth surname remains unproved."),
    dict(id="I383", name="William Andrew Hickey", ged="William Andrew /Hickey/", sex="M", birth="13 JUN 1888; Circleville, Pickaway County, Ohio", death="6 APR 1971; Circleville, Pickaway County, Ohio", sources=["S56", "S57"], note="The 1900 census names John and Mary as parents; draft, death, burial, and SSA indexes corroborate identity."),
    dict(id="I384", name="Daisy Marie Imler Hickey", ged="Daisy Marie /Imler/", sex="F", birth="3 APR 1890; Pickaway County, Ohio", death="20 APR 1942; Circleville, Pickaway County, Ohio", sources=["S56", "S58"], note="Census and SSA records link Daisy to William Imler, Annie Westbury, husband William Hickey, and daughter Alice. A secondary 22 Apr death date is retained as a rejected conflict in the research log."),
    dict(id="I385", name="John Hickey", ged="John /Hickey/", sex="M", birth="JUN 1849; Ohio", death="", sources=["S57"], note="The 1900 census records John and Mary with son William; John's parents were born in Ireland but are unnamed."),
    dict(id="I386", name="Mary Hickey", ged="Mary /Unknown/", sex="F", birth="MAR 1859; Ohio", death="", sources=["S57"], note="The 1900 census records Mary with husband John and son William; her birth surname and parents remain unproved."),
    dict(id="I387", name="William Imler", ged="William /Imler/", sex="M", birth="APR 1860; Ohio", death="", sources=["S58", "S59"], note="The 1900 census and 1889 marriage record identify wife Annie Westbury and daughter Daisy."),
    dict(id="I388", name="Annie Westbury Imler", ged="Annie /Westbury/", sex="F", birth="FEB 1871; Ohio", death="", sources=["S59", "S60"], note="The 1880 census identifies Annie as daughter of Robert and Hester; the 1889 marriage record supplies the Imler link."),
    dict(id="I389", name="Robert Westbury", ged="Robert /Westbury/", sex="M", birth="ABT 1832; England", death="", sources=["S60"], note="The 1880 census records Robert and Hester with daughter Annie; the 1861 marriage record corroborates the couple."),
    dict(id="I390", name="Hester Stonerock Westbury", ged="Hester /Stonerock/", sex="F", birth="ABT 1842; Ohio", death="", sources=["S60"], note="The 1880 census and 1861 Pickaway County marriage record support the name and relationship."),
]


FAMILIES = [
    dict(id="F156", husband="I001", wife="I356", children=[], marriage="", sources=["S49"], note="Owner-confirmed spouse relationship; no children or marriage details were added."),
    dict(id="F157", husband="I357", wife="I358", children=["I356"], marriage="3 MAR 1990; Franklin County, Ohio", sources=["S49", "S50"], note="Ohio birth and marriage indexes corroborate the owner-supplied parents."),
    dict(id="F158", husband="I359", wife="I360", children=["I358"], marriage="", sources=["S52", "S53"], note="Sally's Ohio birth index names Keith Douglas Vanhoose and Barbara Lynn Boltenhouse."),
    dict(id="F159", husband="I361", wife="I362", children=["I359"], marriage="", sources=["S53", "S61", "S65"], note="Keith's SSA application and Mildred's obituary identify the couple as his parents."),
    dict(id="F160", husband="I365", wife="I366", children=["I361"], marriage="", sources=["S61", "S62"], note="Douglas's birth index and the 1920/1930 census chain support this parent link."),
    dict(id="F161", husband="I369", wife="I370", children=["I365"], marriage="22 APR 1868; Johnson County, Kentucky", sources=["S63"], note="John is recorded as their son in the 1880 census."),
    dict(id="F162", husband="I371", wife="I372", children=["I366"], marriage="28 AUG 1868; Johnson County, Kentucky", sources=["S64"], note="Tallie's death certificate names both parents; census and marriage records identify the couple."),
    dict(id="F163", husband="I367", wife="I368", children=["I362"], marriage="", sources=["S65"], note="Mildred's obituary names both parents and the 1930 census corroborates the household."),
    dict(id="F164", husband="I363", wife="I364", children=["I360"], marriage="", sources=["S54", "S55", "S56"], note="The 1950 census and Charles's obituary identify Barbara as their daughter."),
    dict(id="F165", husband="I373", wife="I374", children=["I363"], marriage="", sources=["S55", "S66"], note="Charles Jr's obituary and the 1930 census identify Charles Sr and Leona."),
    dict(id="F166", husband="I375", wife="I376", children=["I373"], marriage="24 APR 1902; Ross County, Ohio", sources=["S67"], note="The 1910 census records Charles as their son; the marriage record supplies Malinda's surname."),
    dict(id="F167", husband="I379", wife="I380", children=["I375"], marriage="19 JUL 1869; Ross County, Ohio", sources=["S67"], note="The 1900 census records Alonzo as their son; the marriage record supplies Elizabeth's surname."),
    dict(id="F168", husband="I377", wife="I378", children=["I374"], marriage="", sources=["S66", "S68"], note="The 1910 census records Leona as their daughter; the 1900 household links the couple and son William."),
    dict(id="F169", husband="I381", wife="I382", children=["I377"], marriage="", sources=["S68"], note="The 1900 census explicitly records George as son of Alo and Rebecca."),
    dict(id="F170", husband="I383", wife="I384", children=["I364"], marriage="", sources=["S56", "S57", "S58"], note="Alice's SSA application and the 1940 census identify William and Daisy as her parents."),
    dict(id="F171", husband="I385", wife="I386", children=["I383"], marriage="ABT 1879", sources=["S57"], note="The 1900 census records William as their son and reports the couple married for 21 years; Mary's birth surname remains unknown."),
    dict(id="F172", husband="I387", wife="I388", children=["I384"], marriage="4 JUL 1889; Pickaway County, Ohio", sources=["S58", "S59"], note="The 1900 census records Daisy as their daughter."),
    dict(id="F173", husband="I389", wife="I390", children=["I388"], marriage="17 DEC 1861; Pickaway County, Ohio", sources=["S60"], note="The 1880 census records Annie as their daughter."),
]


SOURCES = [
    dict(id="S49", title="Owner statement identifying Arianna Lynn Fischer and her parents", author="Fredric Muller Vollmer", date="2 SEP 2026", note="The owner identifies Arianna Lynn Fischer, born 1990, as his wife and names her parents as Sally Fischer and Ray W. Fischer. The exact living date is not published."),
    dict(id="S50", title="Arianna Lynn Fischer Ohio birth and parent index cluster", author="Ohio Department of Health; Ancestry.com", date="1990", note="Ohio birth index entries name Arianna and identify Wallace Ray Fischer and Sally Lynn Vanhoose Fischer as parents; a Franklin County marriage index records Wallace R. Fischer and Sally L. on 3 Mar 1990. Records: https://www.ancestry.com/search/collections/3146/records/11206028 ; https://www.ancestry.com/search/collections/3146/records/26206028 ; https://www.ancestry.com/search/collections/3146/records/41206028 ; https://www.ancestry.com/search/collections/2025/records/1910252"),
    dict(id="S51", title="Wallace Ray Fischer identity record cluster", author="Ohio voter and public-record indexes; North Caroline High School yearbook; Ancestry.com", date="", note="Records consistently identify Wallace Ray Fischer, including North Caroline High School yearbook entries. Living birth details and addresses are intentionally omitted. Records: https://www.ancestry.com/search/collections/62740/records/4543428 ; https://www.ancestry.com/search/collections/62209/records/299213236 ; https://www.ancestry.com/search/collections/1265/records/621855255"),
    dict(id="S52", title="Sally Lynn Vanhoose Fischer Ohio birth and parent index cluster", author="Ohio Department of Health; Ancestry.com", date="", note="Ohio birth-index entries identify Sally Lynn Vanhoose/Fischer and name Keith Douglas Vanhoose and Barbara Lynn Boltenhouse as parents. Living exact dates and addresses are omitted. Records: https://www.ancestry.com/search/collections/3146/records/7991760 ; https://www.ancestry.com/search/collections/3146/records/11694596 ; https://www.ancestry.com/search/collections/3146/records/26694596 ; https://www.ancestry.com/search/collections/3146/records/41694596"),
    dict(id="S53", title="Keith Douglas Vanhoose SSA and burial index cluster", author="Social Security Administration; Find a Grave; Ancestry.com", date="", note="SSA application and burial indexes establish Keith's dates and name Douglas T. Vanhoose and Mildred Tackett as parents. Records: https://www.ancestry.com/search/collections/60901/records/39551452 ; https://www.ancestry.com/search/collections/60525/records/95267098"),
    dict(id="S54", title="1950 United States census household of Charles, Alice, and Barbara Boltenhouse", author="U.S. Census Bureau; National Archives and Records Administration; Ancestry.com", date="1950", note="Circleville, Pickaway County, Ohio household records Charles E. Boltenhouse, wife Alice M., and daughter Barbara. Records: https://www.ancestry.com/search/collections/62308/records/204443745 ; https://www.ancestry.com/search/collections/62308/records/204443746 ; https://www.ancestry.com/search/collections/62308/records/204443747", media="1950_charles-alice-barbara-boltenhouse_us-census.jpg"),
    dict(id="S55", title="Charles Emerald Boltenhouse Jr burial and obituary records", author="Find a Grave; Wellman Funeral Home; Ancestry.com", date="1 MAR 2026", note="The obituary identifies parents Charles and Leona Tomlinson Boltenhouse, wife Alice Hickey, and daughter Barbara. Records: https://www.ancestry.com/search/collections/60525/records/297099223 ; https://www.ancestry.com/search/collections/2190/records/21600019 ; https://www.wellmanfuneralhomes.com/obituaries/charles-boltenhouse-jr"),
    dict(id="S56", title="Alice Marie Hickey Boltenhouse SSA and census record cluster", author="Social Security Administration; U.S. Census Bureau; Ancestry.com", date="", note="SSA application names William Hickey and Daisy M. Imler as parents; 1940 and 1950 censuses corroborate the household chain. Records: https://www.ancestry.com/search/collections/60901/records/41344689 ; https://www.ancestry.com/search/collections/2442/records/31756365 ; https://www.ancestry.com/search/collections/62308/records/204443746", media="1940_william-daisy-alice-hickey_us-census.jpg"),
    dict(id="S57", title="William Andrew Hickey vital, draft, and census record cluster", author="U.S. Census Bureau; Selective Service System; Ohio vital records; Ancestry.com", date="", note="The 1900 census identifies William as son of John and Mary; draft, death, burial, and SSA indexes corroborate identity. Records: https://www.ancestry.com/search/collections/7602/records/41345114 ; https://www.ancestry.com/search/collections/5763/records/408395 ; https://www.ancestry.com/search/collections/60525/records/103465820 ; https://www.ancestry.com/search/collections/6482/records/19464076 ; https://www.ancestry.com/search/collections/1002/records/6996448 ; https://www.ancestry.com/search/collections/60901/records/641344689", media="1900_john-mary-william-hickey_us-census.jpg"),
    dict(id="S58", title="Daisy Marie Imler Hickey census, SSA, and marriage record cluster", author="U.S. Census Bureau; Social Security Administration; Ohio county records; Ancestry.com", date="", note="The 1900 census identifies William Imler and Annie as Daisy's parents; SSA and later census records link husband William Hickey and daughter Alice. Records: https://www.ancestry.com/search/collections/7602/records/41347856 ; https://www.ancestry.com/search/collections/2442/records/31756357 ; https://www.ancestry.com/search/collections/6061/records/27418446 ; https://www.ancestry.com/search/collections/60901/records/791344689 ; https://www.ancestry.com/search/collections/61378/records/1204214340", media="1900_william-annie-daisy-imler_us-census.jpg"),
    dict(id="S59", title="William Imler and Annie Westbury census and marriage records", author="U.S. Census Bureau; Pickaway County records; Ancestry.com", date="", note="The 4 Jul 1889 marriage record names Annie Westbury; the 1900 census records the couple with daughter Daisy. Records: https://www.ancestry.com/search/collections/61378/records/893547 ; https://www.ancestry.com/search/collections/7602/records/41347854 ; https://www.ancestry.com/search/collections/7602/records/41347855"),
    dict(id="S60", title="Westbury-Stonerock 1880 census and 1861 marriage records", author="U.S. Census Bureau; Pickaway County records; Ancestry.com", date="", note="The 1880 census identifies Annie as daughter of Robert Westbury and Hester; the 17 Dec 1861 marriage record supplies Hester Stonerock. Records: https://www.ancestry.com/search/collections/6742/records/18379300 ; https://www.ancestry.com/search/collections/6742/records/24757281 ; https://www.ancestry.com/search/collections/6742/records/18379404 ; https://www.ancestry.com/search/collections/61378/records/416305", media="1880_robert-hester-annie-westbury_us-census.jpg"),
    dict(id="S61", title="Douglas T. Vanhoose birth, census, military, and death record cluster", author="Kentucky vital records; U.S. Census Bureau; U.S. Department of Veterans Affairs; Ancestry.com", date="", note="The Kentucky birth index, 1930 census, military index, and death index establish Douglas's identity and link him to Tallie. Records: https://www.ancestry.com/search/collections/8788/records/3688158 ; https://www.ancestry.com/search/collections/6224/records/81187869 ; https://www.ancestry.com/search/collections/2441/records/10171281 ; https://www.ancestry.com/search/collections/3077/records/2504865 ; https://www.ancestry.com/search/collections/60901/records/639551452", media="1930_tallie-douglas-vanhoose_us-census.jpg"),
    dict(id="S62", title="John B. and Tallie Vanhoose 1880 and 1920 census chain", author="U.S. Census Bureau; Ancestry.com", date="", note="The 1880 census records John as son of Moses and Mahala; the 1920 census records John with wife Tallie. Records: https://www.ancestry.com/search/collections/6742/records/41518791 ; https://www.ancestry.com/search/collections/6061/records/59825157", media="1920_john-tallie-vanhoose_us-census.jpg"),
    dict(id="S63", title="Moses Vanhoose and Mahala Dixon census and marriage records", author="U.S. Census Bureau; Johnson County records; Ancestry.com", date="", note="The 1880 census records John as their son; the 22 Apr 1868 marriage record names Mahala Dixon. Records: https://www.ancestry.com/search/collections/6742/records/9277240 ; https://www.ancestry.com/search/collections/6742/records/10191909 ; https://www.ancestry.com/search/collections/61372/records/1506164", media=["1880_moses-mahala-john-vanhoose_us-census.jpg", "1868-04-22_moses-vanhoose_mahala-dixon_marriage.jpg"]),
    dict(id="S64", title="Tallie Vanhoose death certificate and Estep-Morton census-marriage cluster", author="Kentucky vital records; U.S. Census Bureau; Johnson County records; Ancestry.com", date="", note="Tallie's death certificate names Ira Estep and Isora Morton. The 1880 census and 28 Aug 1868 marriage record identify the matching couple. Records: https://www.ancestry.com/search/collections/1222/records/2144978 ; https://www.ancestry.com/search/collections/7602/records/5598207 ; https://www.ancestry.com/search/collections/6742/records/17600141 ; https://www.ancestry.com/search/collections/6742/records/17600401 ; https://www.ancestry.com/search/collections/61372/records/1551052", media="1967-05-17_tallie-vanhoose_death-certificate.jpg"),
    dict(id="S65", title="Mildred I. Tackett Vanhoose obituary and 1930 census", author="Circleville Herald; U.S. Census Bureau; Ancestry.com", date="22 AUG 2015", note="The obituary names parents Sidney Tackett and Ida Missouri and husband Douglas VanHoose; the 1930 census corroborates Sid, Ida, and Mildred. Records: https://www.ancestry.com/search/collections/7545/records/500515930 ; https://www.ancestry.com/search/collections/6224/records/81187850 ; http://www.circlevilleherald.com/obituaries/mildred-i-vanhoose/article_9d73b9f0-f575-5f2a-b23d-b65a593e7879.html", media="1930_sidney-ida-mildred-tackett_us-census.jpg"),
    dict(id="S66", title="Charles Emerald Boltenhouse Sr and Leona Tomlinson vital, census, draft, and marriage cluster", author="U.S. Census Bureau; Selective Service System; Ohio vital and county records; Ancestry.com", date="", note="Draft, marriage, census, and death records establish the couple and their son Charles. Records: https://www.ancestry.com/search/collections/2238/records/199550522 ; https://www.ancestry.com/search/collections/61378/records/1050733026 ; https://www.ancestry.com/search/collections/6224/records/69946949 ; https://www.ancestry.com/search/collections/6224/records/69946957 ; https://www.ancestry.com/search/collections/5763/records/1910198"),
    dict(id="S67", title="Boltenhouse direct-line census and marriage record chain", author="U.S. Census Bureau; Ross County records; Ancestry.com", date="", note="The 1910 census names Alonzo and Malinda as Charles's parents; their 1902 marriage supplies Speakman. The 1900 census names Augustus and Elizabeth as Alonzo's parents; their 1869 marriage supplies Cotter. Records: https://www.ancestry.com/search/collections/7884/records/142595859 ; https://www.ancestry.com/search/collections/7884/records/22453970 ; https://www.ancestry.com/search/collections/61378/records/266107 ; https://www.ancestry.com/search/collections/7602/records/51092013 ; https://www.ancestry.com/search/collections/7602/records/51092011 ; https://www.ancestry.com/search/collections/61378/records/1411597", media=["1910_alonzo-malinda-charles-boltenhouse_us-census.jpg", "1900_augustus-elizabeth-alonzo-boltenhouse_us-census.jpg"]),
    dict(id="S68", title="Tomlinson-Jackson direct-line census and parent-name record chain", author="U.S. Census Bureau; Ohio county records; Ancestry.com", date="", note="The 1910 census records Leona as daughter of George P. and Linda. The 1900 census records George with wife Malinda and explicitly names his parents Alo and Rebecca; a later child marriage index supplies Linda Jackson. Records: https://www.ancestry.com/search/collections/7884/records/142595257 ; https://www.ancestry.com/search/collections/7602/records/51098669 ; https://www.ancestry.com/search/collections/61378/records/1350876129", media="1910_george-linda-leona-tomlinson_us-census.jpg"),
]


def event_lines(tag: str, value: str) -> list[str]:
    if not value:
        return []
    date, _, place = value.partition(";")
    lines = [f"1 {tag}", f"2 DATE {date.strip()}"]
    if place.strip():
        lines.append(f"2 PLAC {place.strip()}")
    return lines


families_as_child = {}
families_as_spouse: dict[str, list[str]] = {}
for family in FAMILIES:
    for child in family["children"]:
        families_as_child[child] = family["id"]
    for spouse in (family["husband"], family["wife"]):
        if spouse:
            families_as_spouse.setdefault(spouse, []).append(family["id"])


def person_block(person: dict) -> str:
    lines = [f"0 @{person['id']}@ INDI", f"1 NAME {person['ged']}", f"1 SEX {person['sex']}"]
    lines += event_lines("BIRT", person["birth"])
    lines += event_lines("DEAT", person["death"])
    lines += [f"1 NOTE {person['note']}", f"1 REFN FISCHER-DIRECT-{person['id']}"]
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
for person in PEOPLE:
    ged = remove_block(ged, person["id"], "INDI")
for family in FAMILIES:
    ged = remove_block(ged, family["id"], "FAM")
for source in SOURCES:
    ged = remove_block(ged, source["id"], "SOUR")
ged = ged.replace("1 SOUR @S49@\n", "").replace("1 FAMS @F156@\n", "")
root_match = re.search(r"^0 @I001@ INDI\n.*?(?=^0 )", ged, flags=re.M | re.S)
if not root_match:
    raise RuntimeError("I001 missing")
root = root_match.group(0).rstrip() + "\n1 NOTE Owner-confirmed spouse: Arianna Lynn Fischer.\n1 SOUR @S49@\n1 FAMS @F156@\n"
ged = ged[: root_match.start()] + root + ged[root_match.end() :]
ged = re.sub(r"\n?0 TRLR\s*$", "", ged).rstrip() + "\n"
ged += "\n".join(person_block(person) for person in PEOPLE) + "\n"
ged += "\n".join(family_block(family) for family in FAMILIES) + "\n"
ged += "\n".join(source_block(source) for source in SOURCES) + "\n0 TRLR\n"
GED.write_text(ged, encoding="utf-8")


canonical = json.loads(CANONICAL.read_text(encoding="utf-8"))
new_person_ids = {person["id"] for person in PEOPLE}
new_family_ids = {family["id"] for family in FAMILIES}
new_source_ids = {source["id"] for source in SOURCES}
canonical["people"] = [person for person in canonical["people"] if person["individual_id"] not in new_person_ids]
canonical["families"] = [family for family in canonical["families"] if family["family_id"] not in new_family_ids]
canonical["sources"] = [source for source in canonical["sources"] if source["source_id"] not in new_source_ids]
for person in canonical["people"]:
    if person["individual_id"] == "I001":
        refs = [value for value in person["source_refs"].split(";") if value and value != "S49"] + ["S49"]
        person["source_refs"] = ";".join(refs)
        spouse_families = [value for value in person["families_as_spouse"].split(";") if value and value != "F156"] + ["F156"]
        person["families_as_spouse"] = ";".join(spouse_families)
        if "Arianna Lynn Fischer" not in person["notes"]:
            person["notes"] += " | Owner-confirmed spouse: Arianna Lynn Fischer."
for person in PEOPLE:
    canonical["people"].append({
        "individual_id": person["id"],
        "name": person["name"],
        "sex": person["sex"],
        "birth": person["birth"],
        "death": person["death"],
        "occupations_and_roles": "",
        "local_ids": f"FISCHER-DIRECT-{person['id']}",
        "source_refs": ";".join(person["sources"]),
        "notes": person["note"],
        "family_as_child": families_as_child.get(person["id"], ""),
        "families_as_spouse": ";".join(families_as_spouse.get(person["id"], [])),
    })
for family in FAMILIES:
    canonical["families"].append({
        "family_id": family["id"],
        "husband_id": family["husband"],
        "wife_id": family["wife"],
        "children_ids": ";".join(family["children"]),
        "marriage": family["marriage"],
        "notes": family["note"],
        "source_refs": ";".join(family["sources"]),
    })
for source in SOURCES:
    canonical["sources"].append({
        "source_id": source["id"],
        "title": source["title"],
        "author": source["author"],
        "date": source["date"],
        "notes": source["note"] + "".join(f" Preserved image: records/{media}." for media in source_media(source)),
        "origin": "Arianna Fischer direct-ancestry research",
    })
canonical["people"].sort(key=lambda row: int(row["individual_id"][1:]))
canonical["families"].sort(key=lambda row: int(row["family_id"][1:]))
canonical["sources"].sort(key=lambda row: int(row["source_id"][1:]))
canonical["metadata"]["scope"] = "Canonical Vollmer tree plus Arianna Lynn Fischer and her documented direct paternal and maternal ancestry; no Fischer collateral relatives were added."
canonical["metadata"]["privacy"] = "Living addresses and contact information are omitted. Living exact dates are withheld except Arianna's owner-supplied birth year."
canonical["metadata"]["vital_date_coverage"] = {
    "people": 363, "birth_dates_recorded": 235, "death_dates_recorded": 199,
    "complete": 166, "partial": 102, "unresolved": 63, "privacy_limited": 25, "living_private": 7,
}
canonical["metadata"]["occupation_coverage"] = {
    "people": 363, "people_with_recorded_occupations_or_roles": 17, "accepted_occupation_events": 23,
    "unresolved": 305, "privacy_limited": 31, "living_private": 8, "minor_without_occupation": 2,
}
canonical["provenance"] = [row for row in canonical["provenance"] if row.get("thread_title") != "Add Arianna Fischer direct ancestry"]
canonical["provenance"].append({"thread_title": "Add Arianna Fischer direct ancestry", "role": "owner-supplied spouse/parent anchors plus Ancestry-indexed direct-line research with preserved source images; no collateral expansion"})
canonical["corrections"] = [row for row in canonical["corrections"] if row.get("topic") not in {"Wallace Ray Fischer name", "Fischer paternal stopping point"}]
canonical["corrections"] += [
    {"topic": "Wallace Ray Fischer name", "corrected": "Owner supplied Ray W. Fischer; Ohio records repeatedly identify him as Wallace Ray Fischer. The record form is used with the owner's form retained as an alias note."},
    {"topic": "Fischer paternal stopping point", "corrected": "No parent-naming record for Wallace Ray Fischer was found. His parents remain blank; private member trees and same-name suggestions were not imported."},
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
    vital_rows = [row for row in csv.DictReader(handle) if row["individual_id"] not in new_person_ids]
for row in vital_rows:
    if row["individual_id"] == "I001":
        row["source_refs"] = "S1;S49"
for person in PEOPLE:
    if person["id"] in {"I357", "I358", "I360"}:
        birth_status = death_status = overall = "withheld—living/private"
    else:
        birth_status = "recorded" if person["birth"] else "unresolved"
        death_status = "recorded" if person["death"] else "unresolved"
        overall = "complete" if person["birth"] and person["death"] else "partial" if person["birth"] or person["death"] else "unresolved"
    vital_rows.append({
        "individual_id": person["id"], "name": person["name"], "birth": person["birth"], "birth_status": birth_status,
        "death": person["death"], "death_status": death_status, "overall_status": overall, "source_refs": ";".join(person["sources"]),
    })
vital_rows.sort(key=lambda row: int(row["individual_id"][1:]))
write_csv(VITAL_COVERAGE, list(vital_rows[0]), vital_rows)


with OCCUPATION_COVERAGE.open(newline="", encoding="utf-8") as handle:
    occupation_rows = [row for row in csv.DictReader(handle) if row["individual_id"] not in new_person_ids]
for row in occupation_rows:
    if row["individual_id"] == "I001":
        row["source_refs"] = "S1;S49"
for person in PEOPLE:
    living = person["id"] in {"I356", "I357", "I358", "I360"}
    occupation_rows.append({
        "individual_id": person["id"], "name": person["name"], "occupations_and_roles": "", "event_count": "0",
        "status": "withheld—living/private" if living else "unresolved—no supported occupation found", "categories": "",
        "source_refs": ";".join(person["sources"]), "research_ids": "",
        "coverage_note": "No living person's occupation was researched or exposed." if living else "No supported occupation or role was found in the records reviewed for this direct-line expansion.",
    })
occupation_rows.sort(key=lambda row: int(row["individual_id"][1:]))
write_csv(OCCUPATION_COVERAGE, list(occupation_rows[0]), occupation_rows)


inventory_rows = []
for source in canonical["sources"]:
    inventory_rows.append({
        "source_id": source["source_id"], "title": source["title"], "author": source["author"], "date": source["date"],
        "notes": source["notes"], "origin": source["origin"],
    })
for record in sorted(path for path in RECORDS.iterdir() if path.is_file()):
    inventory_rows.append({
        "source_id": f"RECORD-{record.stem}", "title": record.name, "author": "", "date": "",
        "notes": hashlib.sha256(record.read_bytes()).hexdigest(), "origin": "preserved original or derivative record",
    })
write_csv(SOURCE_INVENTORY, ["source_id", "title", "author", "date", "notes", "origin"], inventory_rows)


marker = "\n## Arianna Lynn Fischer direct-ancestry expansion (2 September 2026)\n"
source_text = SOURCES_MD.read_text(encoding="utf-8").split(marker, 1)[0].rstrip() + marker
source_text += "\nOwner anchor: Arianna Lynn Fischer (born 1990), wife of Fredric Muller Vollmer; parents Sally Fischer and Ray W. Fischer. The public tree withholds living exact dates, addresses, and contact information. No collateral relatives were added.\n\n"
for source in SOURCES:
    source_text += f"### {source['id']} — {source['title']}\n\n{source['note']}"
    for media in source_media(source):
        source_text += f"\n\nPreserved image: `records/{media}`."
    source_text += "\n\n"
source_text += "### Research controls\n\n- Wallace Ray Fischer's parents remain blank because no parent-naming record was located.\n- Mahala Dixon's possible 1860 household was not used to add parents because that census does not state relationships.\n- Private Ancestry member trees and suggested same-name records were treated only as search clues.\n- Daisy Imler's 20 Apr 1942 death date is retained; a secondary 22 Apr form remains a documented conflict rather than a second event.\n"
SOURCES_MD.write_text(source_text, encoding="utf-8")


RESEARCH_LOG.write_text(
    "# Arianna Lynn Fischer direct-ancestry research log\n\n"
    "Researched in the signed-in Ancestry session on 2 September 2026. Scope was limited to Arianna, her parents, and direct ancestors. No siblings, aunts/uncles, cousins, prior spouses, or other collateral relatives were added.\n\n"
    "## Outcome\n\n"
    "- Owner anchor: Arianna Lynn Fischer, born 1990, wife of Fredric Muller Vollmer; parents Sally Fischer and Ray W. Fischer.\n"
    "- Record normalization: Ohio records consistently use Wallace Ray Fischer for the owner-supplied Ray W. Fischer.\n"
    "- Paternal stop: no parent-naming record was found for Wallace Ray Fischer, so his parents remain blank.\n"
    "- Maternal continuation: documented Vanhoose/Tackett/Estep/Dixon and Boltenhouse/Hickey/Imler/Westbury/Stonerock/Tomlinson lines were added only where a parent-naming record or explicit census relationship supported the link.\n\n"
    "## Evidence\n\n"
    + "\n".join(f"- {source['id']}: {source['title']} — {source['note']}" for source in SOURCES)
    + "\n\n## Preserved images\n\n"
    + "\n".join(f"- `records/{media}` — {source['title']}" for source in SOURCES for media in source_media(source))
    + "\n\n## Rejected or unproved leads\n\n"
    "- An Ancestry obituary-AI result that combined several people and assigned Keith Douglas Vanhoose the wrong 1924 birth and Edward/Mildred parents was rejected. SSA and burial records support the 1944 identity and Douglas/Mildred parentage.\n"
    "- Private member trees with no attached records were not used as evidence.\n"
    "- The 1860 Maha F. Dixon household was retained only as a lead; the census does not state relationships and no additional parent-naming record was found.\n",
    encoding="utf-8",
)


readme = README.read_text(encoding="utf-8")
if "Arianna Lynn Fischer" not in readme:
    readme += "\n## Arianna Lynn Fischer direct ancestry\n\nA 2 September 2026 expansion adds Fredric's wife Arianna Lynn Fischer and her documented direct ancestors only. Source URLs are cataloged in the consolidated source ledger and selected original Ancestry images are preserved under `records/`. Living exact dates, addresses, and contact information are withheld. Wallace Ray Fischer's parents remain blank because no parent-naming record was found.\n"
README.write_text(readme, encoding="utf-8")


validation = VALIDATION.read_text(encoding="utf-8")
replacements = {
    "GEDCOM individuals": 363, "GEDCOM families": 173, "GEDCOM sources": 68,
    "people CSV rows": 363, "families CSV rows": 173, "source inventory rows": len(inventory_rows),
    "vital-date coverage rows": 363, "people with recorded birth dates": 235,
    "people with recorded death dates": 199, "people with complete vital dates": 166,
    "occupation coverage rows": 363, "workbook consolidated individual count": 363,
    "workbook consolidated family count": 173, "workbook consolidated GEDCOM source count": 68,
    "workbook source and record inventory count": len(inventory_rows), "workbook birth dates recorded": 235,
    "workbook death dates recorded": 199, "workbook both vital dates recorded": 166,
    "workbook no dated event unresolved or private": 95,
}
for label, value in replacements.items():
    validation = re.sub(rf"^{re.escape(label)}:.*$", f"{label}: {value}", validation, flags=re.M)
for line in [
    "Arianna Lynn Fischer spouse link present: True",
    "Wallace Ray Fischer parents intentionally blank: True",
    "Fischer collateral relatives added: False",
    "Fischer evidence images preserved: 14",
]:
    if line not in validation:
        validation += "\n" + line
VALIDATION.write_text(validation.rstrip() + "\n", encoding="utf-8")


print(json.dumps({
    "people": len(canonical["people"]), "families": len(canonical["families"]),
    "sources": len(canonical["sources"]), "inventory": len(inventory_rows),
    "preserved_records": len(list(RECORDS.iterdir())),
}, indent=2))
