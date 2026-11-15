# Survival Operations Plan Response

SOPR is an offline-first Raspberry Pi project for serving emergency preparedness, medical, survival, and general reference material on a local network.

The current plan is to build on a fresh Raspberry Pi OS Lite install and automate:

- Base OS preparation
- Required package installation
- Directory layout for content and site assets
- Custom web, admin, and offline PMTiles maps scaffold
- Kiwix ZIM downloads into `/library/zims/content`
- ZIM selection generated from `catalog/kiwix-categories.yaml`

## Current Repository Layout

- `instructions.md` - original project requirements
- `scripts/bootstrap_pi.sh` - prepares a clean Raspberry Pi OS Lite system
- `scripts/install_sopr.sh` - top-level installer for SOPR
- `scripts/build_kiwix_zim_manifest.py` - generates the ZIM manifest from the SOPR curated catalog
- `scripts/download_kiwix_zims.sh` - curated Kiwix ZIM downloader
- `scripts/select_install_profile.sh` - records first-start install choices for optional education add-ons
- `scripts/install_optional_components.sh` - installs optional education components from the selected profile
- `scripts/install_kolibri.sh` - installs Kolibri from Learning Equality's package source
- `scripts/install_ka_lite_legacy.sh` - guarded legacy path for KA Lite requests
- `scripts/configure_access_point.sh` - configures the Pi as a wireless access point for direct client access
- `scripts/install_portal_service.sh` - installs the local portal API service for setup state and live status
- `scripts/install_kiwix_service.sh` - installs and enables the local `kiwix-serve` systemd service
- `scripts/rebuild_kiwix_library.sh` - rebuilds the Kiwix `library.xml` from downloaded ZIM files
- `scripts/run_kiwix_service.sh` - runtime wrapper that starts Kiwix or a placeholder page when the library is empty
- `scripts/install_nginx_site.sh` - installs the Nginx site that serves `/`, `/kiwix`, `/maps`, `/admin`, and `/api`
- `app/sopr_portal.py` - lightweight API for persisted SOPR setup state and Raspberry Pi status
- `config/sopr.env.example` - template for editable install settings
- `config/install-profile.env.example` - template for first-start install profile defaults
- `config/kiwix-zim-urls.quick-test.txt` - tiny starter manifest for fast Kiwix validation
- `catalog/wikipedia.yaml` - selectable Wikipedia ZIM options for the configuration flow
- `docs/architecture.md` - stack and design notes
- `docs/release-checklist.md` - step-by-step validation list for fresh Pi installs and release testing
- `docs/software-plan.md` - software checklist for the Pi
- `index.html.framework` - backup design-language reference for the UI
- `web/admin/index.html` - starter admin page placeholder
- `web/maps/index.html` - offline PMTiles maps viewer powered by MapLibre

## Intended Software Stack

- Raspberry Pi OS Lite
- Kiwix / `kiwix-serve`
- Nginx as the outer landing page / reverse proxy layer
- Avahi for local `.local` discovery on LAN
- Optional wireless AP mode for direct client access
- Custom admin and PMTiles-based maps components built in-repo

This is an initial scaffold for a fully custom stack. It is designed to give us a repeatable starting point on a fresh Pi while keeping the web layer, admin flow, and future maps integration under our control.

## Prepare a Raspberry Pi 4

You need a Raspberry Pi 4, a reliable power supply, an Ethernet connection or Wi-Fi credentials, and a quality microSD card. Use a **128 GB or larger** card for the base system and starter library; choose **256 GB or larger** if you plan to add larger Wikipedia editions, regional maps, or comprehensive ZIM collections.

### 1. Write the operating-system card

1. Install and open [Raspberry Pi Imager](https://www.raspberrypi.com/software/).
2. Select **Raspberry Pi 4**, then select **Raspberry Pi OS Lite (64-bit)** as the operating system.
3. Select the intended microSD card as storage. **Writing the image permanently erases all data on that card.** Confirm the selected capacity and name before continuing.
4. Open the Imager customization settings and set:
   - A username and strong password
   - Hostname: `sopr`
   - Your Wi-Fi network, password, and wireless country (if not using Ethernet)
   - **Enable SSH** so the Pi can be configured remotely
5. Write the card, eject it cleanly, insert it into the Pi, connect networking, and power it on.

For the first installation, Ethernet is recommended: the installer downloads system packages and optional offline content.

### 2. Connect to the Pi

Wait a few minutes for the first boot, then from another computer on the same network run:

```bash
ssh <your-username>@sopr.local
```

If `sopr.local` does not resolve, find the Pi's address in your router's connected-device list and use `ssh <your-username>@<pi-ip>` instead.

### 3. Update the operating system

Before installing SOPR, update the newly installed operating system and reboot so any kernel or firmware update is active:

```bash
sudo apt update
sudo apt full-upgrade -y
sudo apt install -y git
sudo reboot
```

Reconnect with SSH after the Pi has restarted:

```bash
ssh <your-username>@sopr.local
```

### 4. Clone and configure SOPR

On the Raspberry Pi:

```bash
git clone https://github.com/A2ThreeD/sopr-offline-knowledge.git sopr
cd sopr
cp config/sopr.env.example config/sopr.env
nano config/sopr.env
```

For a first validation, retain or set these safe starter values:

```ini
SOPR_HOSTNAME=sopr
SOPR_ZIM_PROFILE=essential
SOPR_ZIM_MODE=quick-test
SOPR_AP_ENABLED=0
```

`quick-test` selects a small test library. It lets you validate Kiwix and the web interface before committing the card and network connection to the complete content download. Leave wireless access-point mode disabled until the normal LAN installation has been verified.

### 5. Install and verify the base system

```bash
sudo ./scripts/install_sopr.sh &&
  systemctl status sopr-portal.service sopr-kiwix.service nginx.service --no-pager
```

The installer prints `SOPR base installation complete.` when it finishes. If it stops earlier, use the first error from the installer output to diagnose the failure.

Download the selected quick-test library:

```bash
sudo ./scripts/download_kiwix_zims.sh
```

Open `http://sopr.local/` in a browser, or use the Pi's IP address if local-name discovery is unavailable. Complete the first-start setup in the browser when ready for the full library and United States maps. Complete Setup downloads coverage for all 50 states, including Alaska, the western Aleutians, and Hawaii. After setup, use **Settings → Maps** for additional countries and custom regions.

### 6. Download the full offline library

After the quick-test system is working, edit `config/sopr.env`, change `SOPR_ZIM_MODE` to `full`, select the desired profile and Wikipedia edition, then run:

```bash
sudo ./scripts/download_kiwix_zims.sh
```

The ZIM library is stored at `/library/zims/content`. Large libraries can take considerable time and storage; keep the Pi powered and connected to the network until the download finishes. If a download fails, SOPR reports the failed URL, continues with the remaining content, and continues the installation. Run the download again to retry; incomplete downloads are kept in `.sopr-download-tmp` in the destination directory. SOPR downloads up to three ZIM files at a time by default. Set `SOPR_ZIM_DOWNLOAD_JOBS` to `1`, `2`, or `3` in `config/sopr.env`. Existing ZIM files remain available during a refresh, which downloads a fresh copy before replacing them and therefore requires additional time and free space.

### OS-only preparation

If you want to install only the required operating-system packages before installing the full SOPR stack:

```bash
sudo ./scripts/bootstrap_pi.sh
```

## Notes

- The installer now assumes a custom stack with no IIAB dependency.
- `catalog/kiwix-categories.yaml` is the source of truth for curated ZIM selection.
- The generated manifest in `config/kiwix-zim-urls.txt` is built from that YAML catalog using `PREPMASTER_ZIM_PROFILE`.
- The selected Wikipedia variant is controlled by `PREPMASTER_WIKIPEDIA_OPTION` and sourced from `catalog/wikipedia.yaml`.
- Supported profiles are `essential`, `standard`, and `comprehensive`. Standard adds Wikipedia Medicine without images, Appropedia, Post-Disaster Library, Sustainable Living Q&A, Hundred Rabbits, CD3WD, Low-tech Magazine, and Electronics Q&A. Comprehensive inherits those titles.
- **Settings → Content → Check Online Catalog** browses the Debian Kiwix mirror by default. The first refresh runs in the background. **Download Selected ZIMs** queues available selections and reports unavailable ones when the catalog is current.
- The home page is a vertical stack of cards. Project Gutenberg Library opens its Kiwix collection, and Medical & First Aid, Food and Water, Survival & Shelter, Repair, Communication, and Power and Energy open topic filters. Settings is the last card. Library rebuilds refresh the SOPR topic tags.
- Set `SOPR_ZIM_MODE=quick-test` if you want a small validation download before pulling the full content set.
- The main page is now intended to be a first-start configuration screen with base install selected by default.
- The main page now switches automatically between first-start setup mode and the normal dashboard based on saved setup state.
- The setup page can now save preferences and trigger the backend apply workflow directly from the browser.
- Kiwix runs on a dedicated local port behind the main site's Nginx proxy.
- If no Kiwix library exists yet, the dedicated Kiwix port serves a placeholder page instead of crash-looping.
- `/maps` now expects a local PMTiles archive under the configured PMTiles root and renders it through MapLibre instead of a raster `z/x/y.png` tile tree.
- Optional education add-ons are tracked separately: `Kolibri` as a modern add-on, and `KA Lite` as a legacy add-on.
- `Kolibri` now has install automation in the repo. `KA Lite` requires an explicit legacy override and currently records the request rather than forcing a risky unattended install on modern Raspberry Pi OS.
- Wireless AP mode can be enabled through `config/sopr.env` and applied by the installer or `scripts/configure_access_point.sh`.
- The installer now provisions `kiwix-serve`, the portal API, and an Nginx site so `/`, `/maps`, `/admin`, and `/api` are served on the main site, and Nginx proxies `/kiwix/` to the local Kiwix service.
- The interface uses the device's standard system font.
- Scrollable panels use white scrollbars on a dark track as a shared SOPR design rule. New scrollable boxes should keep that treatment for consistency.
- User-facing UI should describe upstream sources in generic terms like `regional map catalog` or `offline map packages` rather than adopting another project's branding as a primary label. Source attribution can still live in documentation or secondary status text when needed.

## Build custom offline maps

SOPR can extract a region from a larger Protomaps basemap and install it alongside catalog maps. MapLibre renders the resulting local archive through Nginx.

1. The SOPR base installer installs the Protomaps CLI on 64-bit Raspberry Pi OS and Debian AMD64, checking the checksum before installing. For a manual install, download the [Protomaps `pmtiles` CLI](https://github.com/protomaps/go-pmtiles/releases) on the SOPR server. Choose the release for its OS and architecture (typically Linux ARM64 on a 64-bit Raspberry Pi OS install). Install the extracted binary with `sudo install -m 0755 pmtiles /usr/local/bin/pmtiles`.
2. SOPR finds a recent [Protomaps daily build](https://maps.protomaps.com/builds/) automatically. To use your own source or pin a build, set `SOPR_MAP_BUILD_SOURCE` in `config/sopr.env` to an absolute path to a local archive, such as `/library/sources/planet.pmtiles`, or copy a dated HTTPS URL from [Protomaps Builds](https://maps.protomaps.com/builds/). Keep the local source outside the installed maps folder so it stays out of the map picker. The source must be a clustered PMTiles v3 MVT archive with Protomaps basemap layers. The local source works offline. A remote source needs an internet connection and an HTTPS server that supports byte-range requests.
3. Open **Settings → Maps → Build a Custom Map**. Enter a name, bounds in west, south, east, north order, and the maximum zoom. You can start with the current rectangle by choosing **Build Map From This View** in the map viewer. For an area spanning the date line, build one map for each side. The default maximum zoom is 13. A larger rectangle or higher maximum zoom can increase build time and storage considerably.
4. Follow the job log in Settings. A successful build appears under **Installed Map Regions** in Settings and **Custom Maps** in the viewer. SOPR selects it automatically if there is no valid active archive. The resulting `custom-<name>.pmtiles` is stored in the selected map install location and can be copied to another SOPR installation.

For country maps, open **Settings → Maps → Available Countries**. Filter by country name or ISO code, or use a quick-pick bundle. The picker shows estimated download size and free space on the selected destination. **Install Selected** extracts one country at a time through zoom 15, leaves existing maps in place, and skips countries already installed. Use **Map Jobs** to check progress or cancel the current extract and remaining queue. Any completed country maps stay installed and appear under **Country Maps** in the viewer. Country coverage uses bounding boxes, which can include neighboring areas.

The country bounds, bundles, and size estimates are based on the [PrepperPi catalog](https://github.com/jmarler/prepperpi/blob/998a8f1c0beed00975b539c16acfeddd90f61c3a/services/prepperpi-tiles/regions.json), published under [MIT-0](https://github.com/jmarler/prepperpi/blob/998a8f1c0beed00975b539c16acfeddd90f61c3a/LICENSE). SOPR bundles the catalog for offline access, clips Antarctica’s south bound to Web Mercator’s limit, and extends United States coverage beyond the continental archive.

This workflow extracts existing vector tiles. Generating tiles from raw OSM extracts, arbitrary GeoJSON, or imagery requires a separate tile-building tool and a compatible map style.

## Validation

Use [release checklist](docs/release-checklist.md) when validating a fresh SOPR install or preparing a new release.
