# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import csv
import logging
import os
import time

from .utils import build_city_name_index, build_cp_to_cities, find_all_in_index

_logger = logging.getLogger(__name__)

CSV_MUNICIPALITIES = os.path.join(
    os.path.dirname(__file__),
    "data",
    "municipios_ine.csv",
)
CSV_POSTAL_CODES = os.path.join(
    os.path.dirname(__file__),
    "data",
    "codigos_postales_municipios.csv",
)

CPRO_TO_STATE_CODE = {
    "01": "VI",
    "02": "AB",
    "03": "A",
    "04": "AL",
    "05": "AV",
    "06": "BA",
    "07": "PM",
    "08": "B",
    "09": "BU",
    "10": "CC",
    "11": "CA",
    "12": "CS",
    "13": "CR",
    "14": "CO",
    "15": "C",
    "16": "CU",
    "17": "GI",
    "18": "GR",
    "19": "GU",
    "20": "SS",
    "21": "H",
    "22": "HU",
    "23": "J",
    "24": "LE",
    "25": "L",
    "26": "LO",
    "27": "LU",
    "28": "M",
    "29": "MA",
    "30": "MU",
    "31": "NA",
    "32": "OR",
    "33": "O",
    "34": "P",
    "35": "GC",
    "36": "PO",
    "37": "SA",
    "38": "TF",
    "39": "S",
    "40": "SG",
    "41": "SE",
    "42": "SO",
    "43": "T",
    "44": "TE",
    "45": "TO",
    "46": "V",
    "47": "VA",
    "48": "BI",
    "49": "ZA",
    "50": "Z",
    "51": "CE",
    "52": "ML",
}


def run_ine_assignment(env, overwrite=False, dry_run=True):
    """Core logic used by hook and wizard."""
    start = time.perf_counter()
    country = env.ref("base.es", raise_if_not_found=False)
    if not country:
        return {"error": "Country base.es not found"}

    state_model = env["res.country.state"]
    city_model = env["res.city"]

    states = state_model.search([("country_id", "=", country.id)])
    states_by_code = {s.code: s.id for s in states if s.code}
    states_by_cpro = {
        cpro: states_by_code[code]
        for cpro, code in CPRO_TO_STATE_CODE.items()
        if code in states_by_code
    }

    cp_to_cities = build_cp_to_cities(env, country.id, CSV_POSTAL_CODES)
    name_index = build_city_name_index(env, country.id)

    matched_vals = {}
    stats = {
        "rows_total": 0,
        "matched_by_cp": 0,
        "matched_by_existing": 0,
        "matched_by_name": 0,
        "ambiguous_name": 0,
        "not_found": 0,
        "skipped_locked": 0,
        "skipped_existing": 0,
        "written": 0,
    }

    with open(CSV_MUNICIPALITIES, encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file, delimiter=";")
        for row in reader:
            stats["rows_total"] += 1

            codauto = str(row["CODAUTO"]).strip().zfill(2)
            cpro = str(row["CPRO"]).strip().zfill(2)
            cmun = str(row["CMUN"]).strip().zfill(3)
            dc = str(row["DC"]).strip()
            name = (row["NOMBRE"] or "").strip()

            ine_code = f"{cpro}{cmun}"
            state_id = states_by_cpro.get(cpro)

            vals = {
                "ine_code_state": codauto,
                "ine_code_province": cpro,
                "ine_code_municipality": cmun,
                "ine_code_control_digit": dc,
            }

            city_ids = set()

            # 1) por CP
            cp_candidates = cp_to_cities.get(ine_code, set())
            if cp_candidates:
                city_ids |= cp_candidates
                stats["matched_by_cp"] += 1

            # 2) por código ya existente
            if not city_ids:
                domain = [
                    ("country_id", "=", country.id),
                    ("ine_code", "=", ine_code),
                ]
                if state_id:
                    domain.append(("state_id", "=", state_id))
                existing = city_model.search(domain)
                if existing:
                    city_ids |= set(existing.ids)
                    stats["matched_by_existing"] += 1

            # 3) fallback nombre+provincia, solo si 1 candidato
            if not city_ids:
                name_candidates = find_all_in_index(name_index, name, state_id)
                if len(name_candidates) == 1:
                    city_ids |= name_candidates
                    stats["matched_by_name"] += 1
                elif len(name_candidates) > 1:
                    stats["ambiguous_name"] += 1

            if not city_ids:
                stats["not_found"] += 1
                continue

            for city in city_model.browse(list(city_ids)):
                if city.ine_code_locked:
                    stats["skipped_locked"] += 1
                    continue
                if city.ine_code and not overwrite:
                    stats["skipped_existing"] += 1
                    continue
                matched_vals[city.id] = vals

    if not dry_run:
        for city in city_model.browse(list(matched_vals.keys())):
            city.write(matched_vals[city.id])
            stats["written"] += 1

    stats["elapsed_seconds"] = round(time.perf_counter() - start, 3)
    return stats
