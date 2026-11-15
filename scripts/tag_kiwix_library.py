#!/usr/bin/env python3
# SOPR Offline Knowledge
# Copyright (c) 2026 Aaron Morris / A2ThreeD.
# Add SOPR dashboard tags to the local Kiwix library index.

import os
from pathlib import Path
import re
import sys
import tempfile
import xml.etree.ElementTree as ET


MEDICAL = re.compile(
    r"^(?:zimgit-medicine|nhs\.uk_en_medicines|wwwnc\.cdc\.gov|medlineplus\.gov|"
    r"fas-military-medicine|wikem|mdwiki|librepathology|libretexts\.org_en_med|"
    r"medicalsciences\.stackexchange\.com|ted_mul_tedmed|wikipedia_[a-z]+_medicine)(?:[_\.]|$)"
)
TOPIC_PATTERNS = {
    "sopr-survival-shelter": (
        r"zimgit-(?:post-disaster|survival|shelter|knots)|(?:www\.)?ready\.gov|"
        r"canadian[-_]prep(?:per)?_(?:en_)?(?:winterprepping|bugoutroll|bugoutconcepts)|"
        r"urban-prepper|appropedia|cd3wdproject\.org|wikipedia_[a-z]+_knots"
    ),
    "sopr-repair": r"ifixit|restarters|(?:diy|mechanics|woodworking)\.stackexchange\.com",
    "sopr-communication": r"ham\.stackexchange\.com|repeaterbook|zimgit-(?:radio|communications?)",
    "sopr-power-energy": (
        r"appropedia|(?:sustainability|electronics)\.stackexchange\.com|100r\.co|"
        r"cd3wdproject\.org|solar\.lowtechmagazine\.com|zimgit-(?:power|energy)"
    ),
    "sopr-food-water": (
        r"zimgit-(?:food-preparation|water)|foss\.cooking|based\.cooking|"
        r"(?:cooking|gardening)\.stackexchange\.com|gutenberg_en_lcc-s|"
        r"canadian[-_]prep(?:per)?_(?:en_)?preppingfood"
    ),
}
TOPICS = {tag: re.compile(rf"^(?:{pattern})(?:[_\.]|$)") for tag, pattern in TOPIC_PATTERNS.items()}
MANAGED_TAGS = {"sopr-medical", "sopr-sustainment", *TOPICS}


def tag_library(path: Path) -> None:
    tree = ET.parse(path)
    for book in tree.getroot().findall("book"):
        name = book.get("name", "").lower()
        tags = [tag for tag in book.get("tags", "").split(";") if tag and tag not in MANAGED_TAGS]
        if MEDICAL.match(name) or "medical" in tags or "medicine" in tags:
            tags.append("sopr-medical")
        tags.extend(tag for tag, pattern in TOPICS.items() if pattern.match(name))
        book.set("tags", ";".join(tags))

    # Replace the index atomically so readers never encounter a partial XML file.
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as output:
        temporary = Path(output.name)
        try:
            tree.write(output, encoding="utf-8", xml_declaration=True)
            output.flush()
            os.chmod(temporary, path.stat().st_mode & 0o777)
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    tag_library(Path(sys.argv[1]))
