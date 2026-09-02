export const auditDate = '2026-09-02';

export const externalPortraits = {
  I005: {
    status: 'external_photo_page',
    source_name: 'Ancestry member photo',
    source_url:
      'https://www.ancestry.com/imageviewer/collections/2442/images/M-T0627-01890-00597?pid=79840169',
    source_refs: ['S48'],
    rights: 'External, account-gated image; not copied into the repository.',
    note: 'The canonical occupation ledger records an attached member photograph whose caption identifies Arthur Herman Muller as a General Motors engineer.',
  },
  I193: {
    status: 'external_photo_page',
    source_name: 'Philip Brooks McCormick obituary',
    source_url:
      'https://www.legacy.com/obituaries/name/philip-mccormick-obituary?pid=198128174',
    source_refs: ['S27', 'S46'],
    rights: 'External obituary image; not copied into the repository.',
    note: 'The exact-name obituary page is the verified external page associated with Philip Brooks McCormick and includes a portrait area.',
  },
};

const record = (filename, title, ledgerRefs, personIds, options = {}) => ({
  filename,
  title,
  ledger_refs: ledgerRefs,
  person_ids: personIds,
  canonical_source_refs: options.canonical_source_refs ?? ['S26'],
  status: options.status ?? 'supporting',
  note: options.note ?? '',
  source_platforms: options.source_platforms ?? ['Ancestry'],
  page_count: options.page_count ?? (filename.endsWith('.pdf') ? null : 1),
  preview_paths: options.preview_paths ?? [`records/${filename}`],
});

export const evidenceRecords = [
  record(
    '1648-06-15_deborah-hopkins_birth-register.jpg',
    'Deborah Hopkins birth register',
    ['S57'],
    ['I248', 'I251'],
  ),
  record(
    '1667-02-05_ephraim-doane_mary-knowles_marriage-register.jpg',
    'Ephraim Doane and Mary Knowles marriage register',
    ['S54', 'S60'],
    ['I249', 'I250'],
  ),
  record(
    '1682-02-04_joshua-cook_birth-register.jpg',
    'Joshua Cooke birth register',
    ['S51'],
    ['I245', 'I247', 'I248'],
  ),
  record(
    '1682-04_patience-doane_birth-register.jpg',
    'Patience Doane birth register',
    ['S53'],
    ['I246', 'I249', 'I250'],
  ),
  record(
    '1696_joshua-lane_birth-record.jpg',
    'Joshua Lane birth record',
    ['S84'],
    ['I229', 'I233', 'I234'],
  ),
  record(
    '1717_joshua-lane_bathsheba-robie_marriage-record.jpg',
    'Joshua Lane and Bathsheba Robie marriage record',
    ['S82'],
    ['I229', 'I230'],
  ),
  record(
    '1718_samuel-lane_birth-record.jpg',
    'Samuel Lane birth record',
    ['S81'],
    ['I227', 'I229', 'I230'],
  ),
  record(
    '1722_mary-james_birth-record.jpg',
    'Mary James birth record',
    ['S83'],
    ['I228', 'I231', 'I232'],
    {
      note: 'The record supplies Susanna only by given name; no maiden surname is inferred.',
    },
  ),
  record(
    '1741-12-24_samuel-lane_mary-james_marriage.jpg',
    'Samuel Lane and Mary James marriage record',
    ['S77'],
    ['I227', 'I228'],
  ),
  record(
    '1748-02-09_joshua-lane_nh-birth.jpg',
    'Joshua Lane New Hampshire birth record',
    ['S75'],
    ['I225', 'I227', 'I228'],
  ),
  record(
    '1769-11-15_joshua-lane_hannah-tilton_marriage.jpg',
    'Joshua Lane and Hannah Tilton marriage record',
    ['S76'],
    ['I225', 'I226'],
  ),
  record(
    '1771-12-08_stephen-lane_nh-birth.jpg',
    'Stephen Lane New Hampshire birth record',
    ['S73'],
    ['I223', 'I225', 'I226'],
  ),
  record(
    '1774-02-26_levi-cook_birth-register.jpg',
    'Levi Cook birth register',
    ['S49'],
    ['I239', 'I241', 'I242'],
  ),
  record(
    '1779-01-07_betsey-brown_birth-register.jpg',
    'Betsey Brown birth register',
    ['S50'],
    ['I240', 'I243', 'I244'],
  ),
  record(
    '1794-07-24_levi-cook_betsey-brown_marriage-register.jpg',
    'Levi Cook and Betsey Brown marriage register',
    ['S48'],
    ['I239', 'I240'],
  ),
  record(
    '1797-06-05_stephen-lane_lois-currier_marriage.jpg',
    'Stephen Lane and Lois Currier marriage record',
    ['S74'],
    ['I223', 'I224'],
  ),
  record(
    '1807-02-03_mary-lane_nh-birth-card.jpg',
    'Mary Lane New Hampshire birth card',
    ['S44'],
    ['I222'],
    {
      note: 'The card supports the event but leaves locality and parents blank.',
    },
  ),
  record(
    '1840-09-16_stephen-lane_will.jpg',
    'Stephen Lane will',
    ['S72'],
    ['I223', 'I224'],
  ),
  record(
    '1841-05-05_stephen-lane_probate-letters.jpg',
    'Stephen Lane probate letters',
    ['S72'],
    ['I223', 'I224'],
  ),
  record(
    '1846-10-30_levi-cook_will_genesee.jpg',
    'Levi Cook will and probate',
    ['S47'],
    ['I239', 'I238'],
  ),
  record(
    '1862_peter-william-mcnaughton_civil-war-town-register.jpg',
    'Peter William McNaughton Civil War town register',
    ['S28'],
    ['I265'],
  ),
  record(
    '1868_relief-mcnaughton_dependent-pension-numerical-index.jpg',
    'Relief McNaughton dependent-pension numerical index',
    ['S80'],
    ['I267'],
    {
      source_platforms: ['Fold3', 'NARA'],
      note: 'The numerical index names evidence-only soldier William W McNaughton and corroborates Relief McNaughton’s dependent-mother pension card.',
    },
  ),
  record(
    '1882-08-21_henry-vollmer_arrival-main.jpg',
    'Henry Vollmer arrival on the Main',
    ['S12'],
    ['I208'],
    {
      status: 'supporting_with_uncertainty',
      note: 'The manifest supports Henry’s arrival; adjacency does not prove the relationships of Mary and Louise.',
    },
  ),
  record(
    '1882-08-21_vollmer-family_arrival-main_page-0289.jpg',
    'Vollmer entries on the Main passenger manifest',
    ['S12'],
    ['I208'],
    {
      status: 'supporting_with_uncertainty',
      note: 'The adjacent entries are preserved without inferring a relationship.',
    },
  ),
  record(
    '1883-08-12_themes-pepper_anna-stelling_marriage-certificate.pdf',
    'Themes Peper and Anna Sophie Stelling marriage certificate',
    ['S34'],
    ['I212', 'I213', 'I214', 'I215', 'I216', 'I217'],
    {
      page_count: 2,
      preview_paths: [
        'record-previews/1883-08-12_themes-pepper_anna-stelling_marriage-certificate-1.jpg',
        'record-previews/1883-08-12_themes-pepper_anna-stelling_marriage-certificate-2.jpg',
      ],
      source_platforms: ['New York City Municipal Archives', 'Ancestry'],
    },
  ),
  record(
    '1884-03-14_female-pepper_birth-certificate.pdf',
    'Unnamed female Pepper birth certificate (identified as Metha)',
    ['S33'],
    ['I211', 'I212', 'I213'],
    {
      page_count: 1,
      preview_paths: [
        'record-previews/1884-03-14_female-pepper_birth-certificate-1.jpg',
      ],
      source_platforms: ['New York City Municipal Archives', 'Ancestry'],
      status: 'supporting_with_uncertainty',
      note: 'The original certificate is very high quality for the recorded facts; identifying the unnamed child as Metha is moderate-high confidence.',
    },
  ),
  record(
    '1892_henry-vollmer_ny-state-census.jpg',
    'Excluded 1892 Henry Vollmer household',
    ['X01'],
    [],
    {
      status: 'excluded_identity_control',
      note: 'This household conflicts with Henry John Joseph Vollmer’s original marriage certificate and is not attached to a canonical person.',
    },
  ),
  record(
    '1896_mary-a-mcnaughton_widow-pension-index.jpg',
    'Mary A McNaughton widow-pension index',
    ['S78'],
    ['I268', 'I265'],
    { source_platforms: ['Ancestry', 'NARA'] },
  ),
  record(
    '1901_mayflower-descendant-vol3_john-doane-will.pdf',
    'John Doane will naming son Ephraim',
    ['S64'],
    ['I258', 'I249'],
    {
      page_count: 614,
      preview_paths: [
        'record-previews/1901_mayflower-descendant-vol3_john-doane-will-385.jpg',
      ],
      source_platforms: ['Massachusetts Society of Mayflower Descendants'],
      note: 'The attached preview is PDF page 385, printed page 178, containing the relevant will transcription.',
    },
  ),
  record(
    '1904_mayflower-descendant-vol6_eastham-vital-records.pdf',
    'Eastham vital records: Doane–Knowles family',
    ['S61'],
    ['I249', 'I250', 'I246'],
    {
      page_count: 608,
      preview_paths: [
        'record-previews/1904_mayflower-descendant-vol6_eastham-vital-records-047.jpg',
      ],
      source_platforms: ['Massachusetts Society of Mayflower Descendants'],
      note: 'The attached preview is PDF page 47, printed page 13, containing the marriage and children’s births.',
    },
  ),
  record(
    '1905-08-05_henry-jj-vollmer_marriage-certificate.pdf',
    'Henry John Joseph Vollmer and Metha Peper marriage certificate',
    ['S09'],
    ['I208', 'I211', 'I209', 'I210', 'I212', 'I213'],
    {
      page_count: 2,
      preview_paths: [
        'record-previews/1905-08-05_henry-jj-vollmer_marriage-certificate-1.jpg',
        'record-previews/1905-08-05_henry-jj-vollmer_marriage-certificate-2.jpg',
      ],
      source_platforms: ['New York City Municipal Archives'],
    },
  ),
  record(
    '1910_frederick-carrie-doris-andrew-marsh_us-census.jpg',
    '1910 Frederick and Carrie Marsh household census',
    ['S14'],
    ['I219', 'I264', 'I218', 'I220', 'I274', 'I277'],
    { source_platforms: ['Ancestry', 'NARA'] },
  ),
  record(
    '1910_henry-madie-charles-vollmer_us-census.jpg',
    '1910 Henry, Metha, and Charles Vollmer household census',
    ['S05', 'S11'],
    ['I208', 'I211', 'I207'],
    { source_platforms: ['Ancestry', 'NARA'] },
  ),
  record(
    '1917-03-10_frederick-g-vollmer_death-certificate.pdf',
    'Frederick Gottlieb Heinrich Vollmer death certificate',
    ['S35'],
    ['I282', 'I209', 'I210'],
    {
      page_count: 2,
      preview_paths: [
        'record-previews/1917-03-10_frederick-g-vollmer_death-certificate-1.jpg',
        'record-previews/1917-03-10_frederick-g-vollmer_death-certificate-2.jpg',
      ],
      source_platforms: ['New York City Municipal Archives', 'Ancestry'],
    },
  ),
  record(
    '1918_henry-john-joseph-volmer_wwi-draft-card.jpg',
    'Henry John Joseph Vollmer First World War draft card',
    ['S10'],
    ['I208'],
    { source_platforms: ['Ancestry', 'NARA'] },
  ),
  record(
    '1919-01-03_madie-vollmer_death-certificate.pdf',
    'Identity control: Madie Vollmer death certificate (not Metha)',
    ['S13', 'VD-R01'],
    ['I208', 'I211'],
    {
      page_count: 2,
      preview_paths: [
        'record-previews/1919-01-03_madie-vollmer_death-certificate-1.jpg',
        'record-previews/1919-01-03_madie-vollmer_death-certificate-2.jpg',
      ],
      source_platforms: ['New York City Municipal Archives'],
      status: 'excluded_identity_control',
      note: 'The certificate belongs to Henry’s later wife Martha/Madie Desselberg and must not be used as Metha Peper Vollmer’s death record.',
    },
  ),
  record(
    '1919-12-17_mary-mcnaughton_ny-death-index.jpg',
    'Mary A McNaughton New York death index',
    ['S40'],
    ['I268'],
    { source_platforms: ['Ancestry', 'New York State'] },
  ),
  record(
    '1940-10-16_charles-frederick-vollmer_wwii-draft-card.jpg',
    'Charles Frederic Vollmer Second World War draft card',
    ['S02'],
    ['I207'],
    { source_platforms: ['Ancestry', 'NARA'] },
  ),
  record(
    '1940_charles-doris-henry-vollmer_us-census.jpg',
    '1940 Charles and Doris Vollmer household census',
    ['S01', 'EF-S01'],
    ['I207', 'I218', 'I176', 'I269'],
    { source_platforms: ['Ancestry', 'NARA'] },
  ),
  record(
    '1950_william-alice-mary-thoren_us-census.jpg',
    '1950 William, Alice, and Mary Alice Thoren household census',
    ['S32'],
    ['I336', 'I337', 'I334'],
    {
      canonical_source_refs: ['S32'],
      source_platforms: ['NARA', '1950 Census'],
    },
  ),
  record(
    'giles-hopkins_17th-century-records_pilgrim-hall.pdf',
    'Giles Hopkins: seventeenth-century records',
    ['S67'],
    ['I251', 'I254', 'I255', 'I248'],
    {
      page_count: 6,
      preview_paths: [1, 2, 3, 4, 5, 6].map(
        (page) =>
          `record-previews/giles-hopkins_17th-century-records_pilgrim-hall-${page}.jpg`,
      ),
      source_platforms: ['Pilgrim Hall Museum'],
    },
  ),
  record(
    'plymouth-colony-records-vol1_1639-marriage.pdf',
    'Plymouth Colony record: Richard Knowles and Ruth Bower marriage',
    ['S63'],
    ['I260', 'I261'],
    {
      page_count: 434,
      preview_paths: [
        'record-previews/plymouth-colony-records-vol1_1639-marriage-151.jpg',
      ],
      source_platforms: ['Wikimedia Commons', 'Plymouth Colony Records'],
      note: 'The attached preview is PDF page 151, printed page 129, containing the marriage entry.',
    },
  ),
  record(
    'relief-mcnaughton_mother-pension-index.jpg',
    'Relief McNaughton dependent-mother pension index',
    ['S79'],
    ['I267'],
    { source_platforms: ['Ancestry', 'NARA'] },
  ),
];

export const externalEvidenceChecks = [
  {
    person_id: 'I355',
    platform: 'Newspapers.com via Ancestry',
    url: 'https://www.ancestry.com/search/collections/61843/records/668386200',
    status: 'index_verified_image_not_archived',
    note: 'The obituary index supplies Peter Vollmer’s exact dates and family links; no licensed clipping image was available to preserve.',
  },
  {
    person_id: 'I219',
    platform: 'Newspapers.com via Ancestry',
    url: 'https://www.ancestry.com/search/collections/61843/records/4961110',
    status: 'index_verified_image_access_blocked',
    note: 'The Frederick Heath Marsh obituary index was retained as a moderate lead; the publisher verification page blocked the original newspaper image.',
  },
  {
    person_id: 'I268',
    platform: 'Newspapers.com via Ancestry',
    url: '',
    status: 'no_exact_match',
    note: 'Exact and relaxed searches found no Caledonia or Livingston County obituary for Mary A McNaughton.',
  },
];
