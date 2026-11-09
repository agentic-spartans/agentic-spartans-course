# Sources and limits

## Real ads

USAJOBS Public Data, retrieved 2026-10-20, not a November 3 search. Original compressed SHA-256: `d2c659eb09a30681d6ab87292d0693025c6990c97d0b00b92b03cd2b58658ca0`. Terms checked November 3, 2026: https://developer.usajobs.gov/guides/terms-of-service . Public Data "may be copied, stored, reformatted, adapted, analyzed, published, redistributed"; prior OPM approval not required. Follow each record's official URL and check current availability before applying. This is an unofficial product not operated, sponsored, approved or endorsed by the U.S. Office of Personnel Management.

The original search used Historic JOA and Announcement Text with `StartPositionCloseDate=2026-10-20` and `EndPositionOpenDate=2026-10-20`, then retained GS grades 1 to 9 and hiring paths public, students or recent graduates. This is a limited federal search, not the whole job market. Original status metadata and date are preserved; under-review records are closed, absent status is unknown. Counts are saved in `manifest.json` and the duplicate map in `duplicate_map.csv`.

Input records: 1362. Canonical real ads: 1362. Identical source-id duplicates removed: 0. Real internship appointment records: 52. Announcements with foreign duty locations: 9. Those are US federal employers abroad, not overseas companies or evidence of work authorization. There are no United Kingdom locations in this snapshot. London preferences are not changed to fill that gap.

Text contains every nonempty saved section, without truncation or summary substitution. Contact email addresses in the text are replaced by `[email removed]` (85 addresses in 65 ads, so the bank download carries no email address); each changed record's `text_sha256` is recomputed. One ad's link to a file on its author's own computer is replaced by `[local file link removed]`. Apply by the official announcement link, not by email. Nonempty section counts: {"conditions": 753, "duties": 1362, "education": 1204, "evaluations": 1362, "hiring_path_explanation": 939, "qualifications": 1362, "requirements": 609, "summary": 1362}. Each record names missing sections. All retained records have summary, duties and qualifications, but this does not certify that every required condition was supplied by the original source. Requirement completeness must still be judged from each ad. Text hashes cover the UTF-8 plain text with section headings.

The historical file did not preserve a salary-currency field or exact retrieval time. Currency remains null; hourly/annual amounts are not converted. Date-only provenance is deliberate. `telework_eligible=N` does not prove onsite work. Only the explicit US remote location label sets remote mode; other work modes remain unknown. Country names map to ISO codes where known; Kosovo stays unknown in the common country field and its original label remains in source_metadata. Original agency/department/location/schedule/type/status/hiring-path/grade metadata is retained in provenance. Where agency is absent, employer uses only the explicitly supplied parent department and records that field choice; it never invents an agency. No GPA or grade-based eligibility rule is imposed.

## Synthetic company examples

8 fictional company examples in `company_examples.jsonl`, made up by the Studio on November 3, 2026. No third-party job text. Every example has a synthetic id/title/text/provenance label and no application URL. These are not known-answer controls or real openings. Compare them only in a separate practice section. Never count or recommend them as real jobs. The controls stay separately in `control_ads.jsonl`.

## Excluded sources

Adzuna, Wikimedia and all for-profit company text are excluded from frozen data by studio's source decision. Public job-board access is not a redistribution licence. British Civil Service data is excluded because no current OGL-covered machine route was confirmed in the bounded check; no bot challenge bypass. No fresh data request, registration, contact, credential use or paid OpenRouter run.
