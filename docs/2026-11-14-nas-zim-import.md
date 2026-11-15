# NAS ZIM import — November 14, 2026

Project: SOPR Offline Knowledge. Maintainer: Aaron Morris / A2ThreeD.

Source: a NAS share mounted on the Mac. Destination: the Pi at `/library/zims/content`.

Aaron requested all usable books, including full English Wikipedia. The inventory identified 43 unique archives with valid ZIM magic and a file size matching the checksum offset recorded in the header. Two were already installed; 41 archives (170,276,334,522 bytes) were selected for transfer. Matching UUIDs were deduplicated, preferring ordinary dated filenames. Different editions with different UUIDs were retained. Header/size checks alone are not full archive integrity validation.

Transfers use rsync over SSH through the mounted NAS share, staging in `.sopr-nas-import` so unfinished copies do not appear in the library. NAS files are not changed or removed.

## Excluded incomplete or non-ZIM files

| File | Finding |
| --- | --- |
| `openZIM_ted_mul_mental-health_.zim` | Not a ZIM archive; only 182 bytes. |
| `openZIM_ted_mul_public-health_.zim` | Not a ZIM archive; only 182 bytes. |
| `openZIM_wikipedia_en_medicine_maxi.zim` | Not a ZIM archive; only 182 bytes. |
| `wikipedia_en_all_maxi_2026-08.zim` | Incomplete: 64,070,376,130 bytes present; header expects 127,418,087,648. |

## Archives selected for transfer

| Source filename | Bytes |
| --- | ---: |
| `devdocs_en_react_2026-02.zim` | 2,700,338 |
| `openZIM_wikiciv_en_all_maxi.zim` | 4,632,130 |
| `openZIM_based.cooking_en_all_.zim` | 15,773,778 |
| `openZIM_restarters_en_all_maxi.zim` | 17,383,911 |
| `wikipedia_en_knots_maxi_2026-01.zim` | 18,569,907 |
| `openZIM_zimgit-water_en_.zim` | 20,924,451 |
| `based.cooking_en_all_2026-11.zim` | 23,023,253 |
| `foss.cooking_en_all_2026-11.zim` | 30,424,458 |
| `Kiwix_wikem_en_all__maxi.zim` | 44,098,910 |
| `openZIM_medicalsciences.stackexchange.com_en_all_.zim` | 60,799,834 |
| `openZIM_ham.stackexchange.com_en_all_.zim` | 75,613,751 |
| `openZIM_librepathology_en_all_maxi.zim` | 80,013,537 |
| `openZIM_fas-military-medicine_en_.zim` | 81,455,189 |
| `zimgit-food-preparation_en_2025-04.zim` | 97,822,565 |
| `openZIM_100r.co_en_all_.zim` | 168,072,299 |
| `wwwnc.cdc.gov_en_all_2024-11.zim` | 178,326,622 |
| `cooking.stackexchange.com_en_all_2026-10.zim` | 238,098,128 |
| `libretexts.org_en_phys_2025-01.zim` | 486,294,453 |
| `openZIM_cd3wdproject.org_en_all_.zim` | 581,165,229 |
| `openZIM_ted_mul_tedmed_.zim` | 610,743,749 |
| `libretexts.org_en_eng_2025-01.zim` | 678,394,631 |
| `libretexts.org_en_math_2025-01.zim` | 780,376,935 |
| `libretexts.org_en_biz_2025-01.zim` | 808,845,154 |
| `canadian-prepper_en_bugoutroll_2026-10.zim` | 879,089,689 |
| `libretexts.org_en_geo_2025-01.zim` | 1,139,477,385 |
| `libretexts.org_en_med_2025-01.zim` | 1,192,567,339 |
| `gutenberg_en_lcc-u_2026-03.zim` | 1,288,016,430 |
| `canadian-prepper_en_winterprepping_2026-08.zim` | 1,341,548,037 |
| `openZIM_canadian_prep_winterprepping_.zim` | 1,341,548,407 |
| `medlineplus.gov_en_all_2025-01.zim` | 1,944,841,111 |
| `openZIM_canadian_prep_preppingfood_en_.zim` | 2,160,665,606 |
| `libretexts.org_en_chem_2025-01.zim` | 2,182,916,266 |
| `canadian-prepper_en_preppingfood_2026-10.zim` | 2,194,586,332 |
| `libretexts.org_en_bio_2025-01.zim` | 2,240,946,728 |
| `urban-prepper_en_all_2026-08.zim` | 2,245,235,674 |
| `openZIM_canadian_prep_bugoutconcepts_.zim` | 2,886,218,237 |
| `canadian-prepper_en_bugoutconcepts_2026-08.zim` | 2,886,219,997 |
| `ifixit_en_all_2025-12.zim` | 3,570,695,757 |
| `libretexts.org_en_human_2025-01.zim` | 3,727,437,628 |
| `gutenberg_en_lcc-s_2026-03.zim` | 4,532,683,039 |
| `wikipedia_en_all_maxi_2026-08(1).zim` | 127,418,087,648 |

## Status

Completed November 14, 2026, at 12:23 PM Pacific. All 41 selected archives (170,276,334,522 bytes) were copied and moved into the live library. The catalog now contains 43 books including the two previously installed archives. The full Wikipedia filename was normalized by removing `(1)`.

The automatic finalizer initially failed because sudo authorization had expired. Completion used SOPR's existing file-manager API to move the staged files and its `rebuild-library` workflow to rebuild the catalog and restart Kiwix; no privilege settings were changed.

Verification: all destination file sizes match the transfer manifest, and all 41 imported UUIDs match the rebuilt Kiwix catalog. The rebuild workflow succeeded at 12:23:22 PM Pacific. Both the Kiwix home page and the full English Wikipedia content page returned HTTP 200. Source header/size checks and rsync transfer checks were supplemented by Kiwix metadata validation during the rebuild; a full internal ZIM checksum scan was not performed.

The earlier failure in `/tmp/sopr-nas-supervisor.log` is historical and superseded by this successful recovery. The privileged finalizer did not create `/srv/sopr/data/nas-import-result.json`; this document and SOPR's successful rebuild status record completion instead.
