# Copyright 2024 OCA Contributors
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import csv as _csv_mod
import logging
import re
import unicodedata

_logger = logging.getLogger(__name__)

_GEONAMES_SUFFIX_RE = re.compile(
    r"\s*\("
    r"(?:Sector Urbano|Casco Urbano|Casco|Diseminado|Zona Urbana|Zona Rural"
    r"|N[úu]cleo(?: Urbano)?|Urbanizaci[oó]n[^)]*|Pedan[íi]a[^)]*"
    r"|Barrio[^)]*|Entidad[^)]*)"
    r"\)\s*$",
    re.IGNORECASE,
)
_ARTICLE_RE = re.compile(
    r"^(.*?),\s*(el|la|los|las|l[´'\u2018\u2019]?|els|les|as|os|a|o|es|un|una)\s*$",
    re.IGNORECASE,
)
_BILINGUAL_RE = re.compile(r"/")
_SLUG_STRIP = re.compile(r"['\u00B4\u2018\u2019\u00B7.,\u2014\-]")


def strip_geonames_suffix(name):
    return _GEONAMES_SUFFIX_RE.sub("", name or "").strip()


def strip_accents(text):
    nfkd = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def slug(text):
    text = strip_geonames_suffix(text or "")
    text = strip_accents(text.lower())
    text = _SLUG_STRIP.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def ine_name_variants(ine_name):
    seen = set()
    result = []

    def _add(value):
        value = re.sub(r"\s+", " ", value or "").strip()
        if value and value not in seen:
            seen.add(value)
            result.append(value)

    name = (ine_name or "").strip()
    if not name:
        return result

    if "/" in name:
        _add(name)
        for part in [item.strip() for item in _BILINGUAL_RE.split(name)]:
            for variant in ine_name_variants(part):
                _add(variant)
        return result

    _add(name)

    match = _ARTICLE_RE.match(name)
    if match:
        body, article = match.group(1).strip(), match.group(2).strip()
        _add(f"{article.title()} {body}")
        _add(f"{article.lower()} {body}")
        _add(f"{strip_accents(article).title()} {strip_accents(body)}")
        _add(f"{strip_accents(article).lower()} {strip_accents(body)}")

    for variant in list(result):
        _add(strip_accents(variant))

    for variant in list(result):
        no_apostrophe = re.sub(r"['\u00B4\u2018\u2019]", " ", variant)
        _add(re.sub(r"\s+", " ", no_apostrophe).strip())

    _add(slug(name))
    return result


def build_city_name_index(env, country_id):
    rows = env["res.city"].search_read(
        domain=[("country_id", "=", country_id)],
        fields=["id", "name", "state_id", "zip_ids"],
    )
    index = {}

    def _add_to_index(city_id, state_id, name):
        key = slug(name)
        if not key:
            return
        entry = (city_id, state_id)
        bucket = index.setdefault(key, [])
        if entry not in bucket:
            bucket.append(entry)

    for row in rows:
        city_id = row["id"]
        name = row["name"] or ""
        state_id = row["state_id"][0] if row["state_id"] else None

        _add_to_index(city_id, state_id, name)

        clean = strip_geonames_suffix(name)
        if clean != name:
            _add_to_index(city_id, state_id, clean)

        for variant in ine_name_variants(clean):
            _add_to_index(city_id, state_id, variant)

    _logger.debug(
        "[INE] build_city_name_index: %d cities, %d slugs",
        len(rows),
        len(index),
    )
    return index


def find_all_in_index(index, ine_name, state_id=None):
    result = set()
    for variant in ine_name_variants(ine_name):
        candidates = index.get(slug(variant), [])
        if not candidates:
            continue
        if state_id:
            state_candidates = {cid for cid, sid in candidates if sid == state_id}
            if state_candidates:
                result |= state_candidates
                continue
        result |= {cid for cid, _sid in candidates}
    return result


def build_cp_to_cities(env, country_id, cp_csv_path):
    """
    Build:
        {
            '01059': {12, 18},
            '28079': {44},
        }

    municipio_id and codigo_postal are normalized to 5 digits.
    """
    mun_cps = {}
    with open(cp_csv_path, encoding="utf-8", newline="") as fh:
        for row in _csv_mod.DictReader(fh):
            municipio_id = str(row["municipio_id"]).strip().zfill(5)
            postal_code = str(row["codigo_postal"]).strip().zfill(5)
            mun_cps.setdefault(municipio_id, set()).add(postal_code)

    _logger.debug(
        "[INE] build_cp_to_cities: %d municipalities in CP CSV",
        len(mun_cps),
    )

    zip_rows = env["res.city.zip"].search_read(
        domain=[("city_id.country_id", "=", country_id)],
        fields=["name", "city_id"],
    )

    cp_to_cities = {}
    for row in zip_rows:
        if not row["city_id"]:
            continue
        postal_code = str(row["name"] or "").strip().zfill(5)
        cp_to_cities.setdefault(postal_code, set()).add(row["city_id"][0])

    _logger.debug(
        "[INE] build_cp_to_cities: %d unique postal codes in res.city.zip",
        len(cp_to_cities),
    )

    mun_to_cities = {}
    for municipio_id, postal_codes in mun_cps.items():
        city_ids = set()
        for postal_code in postal_codes:
            city_ids |= cp_to_cities.get(postal_code, set())
        if city_ids:
            mun_to_cities[municipio_id] = city_ids

    matched = len(mun_to_cities)
    total = len(mun_cps)
    _logger.info(
        """[INE] build_cp_to_cities:\
            %d/%d municipalities resolved by postal code (%.1f%%)""",
        matched,
        total,
        matched / total * 100 if total else 0,
    )
    return mun_to_cities
