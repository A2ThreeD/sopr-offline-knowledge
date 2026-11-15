# SOPR installation repairs — November 14, 2026

Project: SOPR Offline Knowledge. Maintainer: Aaron Morris / A2ThreeD.

Applied to the repository and the Raspberry Pi test installation.

## Changes

- `scripts/download_kiwix_zims.sh`: handle individual `wget` failures without aborting the download batch or the installation. Report each failed URL and repeat the failure list at completion. Download into the destination's `.sopr-download-tmp` directory and move completed files into the library, keeping incomplete transfers available for retry without indexing them as books. Existing library files remain available during a refresh. Refreshing an existing file requires a fresh staged copy, additional download time, and temporary disk space. Configuration, filesystem, and library-rebuild errors still fail the script.
- `scripts/install_kiwix_service.sh`: install `load_env.sh` into the deployed runtime's `scripts` directory. The service wrapper is deployed under `/opt/sopr/app` and resolves its helper under `/opt/sopr/scripts`; the missing helper previously caused a restart loop and Nginx 502 responses.
- `scripts/install_nginx_site.sh`: install the repository's `web/kiwix-skin/viewer.js` into the web root before enabling its Nginx route. The configured override previously pointed to an absent file and returned HTTP 404.
- `readme.md`: document download failure handling, retries, and staging requirements.
- `scripts/install_sopr.sh`: replace the obsolete optional `heroimage.png` copy with the actual `images/sopr.png` used by the home page. Install the bundled Michroma font and its license, which were also missing from the deployed site.

## Pi repairs and verification

- Backed up the four changed installer/downloader scripts and the previous Nginx site configuration on the Pi.
- Deployed the four corrected scripts, installed the missing runtime helper, ran the corrected Nginx installer, and restarted Kiwix. Rebuilt the Kiwix library from the two already downloaded medical ZIMs. Installed the home-page logo, local font, and font license without rerunning the full installer.
- Ran an isolated on-Pi integration check using a temporary local HTTP server: a missing ZIM returned 404, the next request downloaded a real ZIM, `kiwix-manage` rebuilt the temporary library, and the downloader returned exit status 0 with the failed URL reported. Temporary test files were removed.
- Nginx configuration validation passed. Nginx, the portal, and Kiwix were active; no failed systemd units were reported.
- HTTP checks through Nginx returned 200 for the home, admin, maps, Kiwix catalog, reader, medical book content, status API, and system health API. Referenced local scripts/styles checked on the maps, catalog, reader, and medical content pages returned 200 with appropriate content types. These were HTTP checks, not an interactive browser test.
- Shell syntax and repository whitespace checks passed. Deployed script contents were compared with the local repository copies.
- Opened the live Pi home page in a browser and visually confirmed that the SOPR logo and local font render correctly.

## Remaining installation state

### Follow-up: Kiwix online catalog

The public `download.kiwix.org/zim/` index redirected to a general webpage, which the portal cached as an empty successful catalog. Initial catalog construction could also exceed the browser timeout. The portal now reads the direct Kiwix category index for the default root, rejects empty results, builds the catalog in the background, preserves a previous catalog on errors, and reports refresh failures. Custom catalog roots remain supported. Five regression tests cover index routing, empty cache recovery, background refresh, and failure handling. An isolated test on the Pi returned 7,018 entries from Kiwix; the user installed the fix and restarted the portal. The live catalog returned HTTP 200 with all 7,018 entries. A sample download link timed out during a mirror TLS handshake, so a live download was not verified. The original Pi portal and cache were backed up on the Pi.

### Follow-up: simpler interface font

At Aaron's request, replaced Michroma with the standard system sans-serif font on the home, settings, and maps pages. Both headings and body text use the same system font stack; log/code text retains its monospace styling. Removed the custom font declarations and the now-unneeded font installation steps. The restored SOPR logo is unchanged. Updated the repository and deployed pages on the Pi, with backups of the previous pages before replacement.

### Content installation

- The full install's stored status still records the earlier failure at download 3 of 36. It has not been rewritten to imply a successful full installation, and the full content batch has not been rerun during this repair.
- The separate map synchronization was already running and was left running. At the last check, it was downloading California, the second of five selected maps. The Washington PMTiles 404 in the earlier Nginx log occurred before that selected file had downloaded; map completion remains to be checked.
- The unavailable `fas-military-medicine_en_2025-06.zim` URL was not replaced. Its failure now allows later downloads to proceed. Retrying cannot restore an upstream file that remains unavailable.
- Changes are local and deployed to this Pi; no commit, push, or release was performed. The pre-existing modification to `scripts/install_maps_assets.sh` was preserved.

### Follow-up: Debian Kiwix mirror

SOPR now uses `https://cdimage.debian.org/mirror/kiwix.org/zim/` by default for catalog browsing and ZIM downloads. The portal ignores caches from previous catalog roots. The downloader routes standard Kiwix links in existing manifests through Debian while preserving paths, filenames, and custom source URLs. Catalog entries and pinned archive versions still depend on mirror availability.

Deployed to the Pi and restarted the portal. The fresh catalog returned 14,030 entries, and a partial archive request returned HTTP 206 with a valid ZIM signature after Debian redirected it to a regional server. Six catalog regression tests and the downloader syntax check passed.

### Follow-up: home page Kiwix categories

Medical & First Aid and Preparedness & Repair now open filtered Kiwix catalog views. Library rebuilds assign SOPR tags using known archive families and existing topic tags. Open Kiwix clears the saved filter to show the full library. Applied the tags to the live Pi index and verified 10 medical and 20 preparedness or repair results in the filtered feeds.

### Follow-up: stale online catalog selections

An older saved selection could block a new download when the mirror retired that archive. With a current catalog, Download Selected ZIMs now queues the available files and reports which unavailable selections were removed. If the catalog is stale or updating, it asks for a successful refresh before dropping any selection. Deployed to the Pi and confirmed Gutenberg Top is listed in its catalog. Verified that the download handler queues Gutenberg when the old Python DevDocs entry is also selected.

### Follow-up: four archives in the Standard preset

Added Wikipedia Medicine without images to Medicine, and Appropedia, Post-Disaster Library, and Sustainable Living Q&A to Survival & Preparedness. Standard and Comprehensive include all four. Together the archives require about 2.2 GiB. The library rebuild assigns the three preparedness titles to the home page's Preparedness & Repair filter and Wikipedia Medicine to Medical & First Aid.

Installed all four on the Pi and verified their entries in the live Kiwix category feeds.

### Follow-up: more home page Kiwix categories

Added Repair, Communication, Power and Energy, and Food and Water cards with icons and dedicated Kiwix filters. The tags are reassigned on each library rebuild, and a title can appear in a topic filter as well as the broader Preparedness & Repair collection. Verified the four live filters on the Pi, with 2, 1, 3, and 9 results respectively at deployment.

### Follow-up: Survival & Shelter

Replaced the broad Preparedness & Repair card with Survival & Shelter. The dedicated Kiwix filter includes emergency preparedness, shelter, survival guides, and knots. Moved Food and Water directly below Medical & First Aid. Verified the order and all 12 Survival & Shelter results on the Pi.

### Follow-up: power and energy references

Standard and Comprehensive now include Hundred Rabbits, CD3WD, Low-tech Magazine, and Electronics Q&A. Power and Energy includes all four in Kiwix. The Pi already had Hundred Rabbits and CD3WD under imported filenames. Started a two-file download from the Debian mirror for Low-tech Magazine and Electronics Q&A, with a library rebuild and Kiwix restart after the batch. The first transfer was confirmed in progress.
