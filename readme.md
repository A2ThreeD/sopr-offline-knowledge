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
sudo ./scripts/install_sopr.sh
systemctl status sopr-portal.service --no-pager
systemctl status sopr-kiwix.service --no-pager
systemctl status nginx --no-pager
```

Download the selected quick-test library:

```bash
sudo ./scripts/download_kiwix_zims.sh
```

Open `http://sopr.local/` in a browser, or use the Pi's IP address if local-name discovery is unavailable. Complete the first-start setup in the browser.

### 6. Download the full offline library

After the quick-test system is working, edit `config/sopr.env`, change `SOPR_ZIM_MODE` to `full`, select the desired profile and Wikipedia edition, then run:

```bash
sudo ./scripts/download_kiwix_zims.sh
```

The ZIM library is stored at `/library/zims/content`. Large libraries can take considerable time and storage; keep the Pi powered and connected to the network until the download finishes.

### OS-only preparation

If you want to install only the required operating-system packages before installing the full SOPR stack:

```bash
sudo ./scripts/bootstrap_pi.sh
```

## Notes

- The installer now assumes a custom stack with no IIAB dependency.
- `catalog/kiwix-categories.yaml` is the source of truth for curated ZIM selection.
- The generated manifest in `config/kiwix-zim-urls.txt` is built from that catalog JSON using `PREPMASTER_ZIM_PROFILE`.
- The selected Wikipedia variant is controlled by `PREPMASTER_WIKIPEDIA_OPTION` and sourced from `catalog/wikipedia.yaml`.
- Supported profiles are `essential`, `standard`, and `comprehensive`.
- Set `SOPR_ZIM_MODE=quick-test` if you want a small validation download before pulling the full content set.
- The main page is now intended to be a first-start configuration screen with base install selected by default.
- The main page now switches automatically between first-start setup mode and the normal dashboard based on saved setup state.
- The setup page can now save preferences and trigger the backend apply workflow directly from the browser.
- Kiwix now runs on a dedicated port, and the dashboard/admin views expose the real Kiwix target URL.
- If no Kiwix library exists yet, the dedicated Kiwix port serves a placeholder page instead of crash-looping.
- `/maps` now expects a local PMTiles archive under the configured PMTiles root and renders it through MapLibre instead of a raster `z/x/y.png` tile tree.
- Optional education add-ons are tracked separately: `Kolibri` as a modern add-on, and `KA Lite` as a legacy add-on.
- `Kolibri` now has install automation in the repo. `KA Lite` requires an explicit legacy override and currently records the request rather than forcing a risky unattended install on modern Raspberry Pi OS.
- Wireless AP mode can be enabled through `config/sopr.env` and applied by the installer or `scripts/configure_access_point.sh`.
- The installer now provisions `kiwix-serve`, the portal API, and an Nginx site so `/`, `/maps`, `/admin`, and `/api` are served on the main site, while `/kiwix` redirects the browser to the dedicated Kiwix port.
- The current UI typography now self-hosts `Michroma` from `web/fonts/Michroma-Regular.ttf` under the SIL Open Font License. The main display stack is `"Michroma Local", "Michroma", "OCR A Std", "OCR A Extended", "Aldrich", "Eurostile", "Bank Gothic", "Rajdhani", "Cascadia Mono", "Consolas", monospace`, and the body stack is `"Michroma Local", "Michroma", "OCR A Std", "OCR A Extended", "Aldrich", "Cascadia Mono", "Consolas", monospace`.
- Scrollable panels use white scrollbars on a dark track as a shared SOPR design rule. New scrollable boxes should keep that treatment for consistency.
- User-facing UI should describe upstream sources in generic terms like `regional map catalog` or `offline map packages` rather than adopting another project's branding as a primary label. Source attribution can still live in documentation or secondary status text when needed.

## Validation

Use [docs/release-checklist.md](/home/prepper/sopr/docs/release-checklist.md) when validating a fresh SOPR install or preparing a new release.
