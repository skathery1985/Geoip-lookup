import csv
import datetime
import ipaddress
import logging
from ipaddress import ip_network
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from geoip2.database import Reader
from mmdb_writer import MMDBWriter
from netaddr import IPSet

app = FastAPI(title="GeoIP API", version="2.0")

# === Paths ===
CITY_AR_CSV = "./db/GeoLite2-City-Locations.csv"
BLOCKS_CSV = "./db/GeoLite2-City-Blocks-IPv4.csv"
MMDB_OUTPUT = "./db/GeoLite2-City-Custom.mmdb"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Load location labels for use in API ===
arabic_locations = {}  # geoname_id → {city_ar, country_ar, continent_ar}
english_locations = {}  # geoname_id → {city_en, country_en, continent_en, country_iso, continent_code}

def load_location_labels():
    logger.info("Loading location labels...")
    global arabic_locations, english_locations
    arabic_locations = {}
    english_locations = {}
    
    with open(CITY_AR_CSV, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "geoname_id" not in row:
                logger.warning(f"Skipping row without geoname_id: {row}")
                continue
                
            geoname_id = row["geoname_id"]
            if row.get("locale_code") == "ar":
                arabic_locations[geoname_id] = {
                    "continent_name": row.get("continent_name", "غير معروف"),
                    "country_name": row.get("country_name", "غير معروف"),
                    "city_name": row.get("city_name", "غير معروف"),
                    "country_iso_code": row.get("country_iso_code"),
                    "continent_code": row.get("continent_code")
                }
            else:
                english_locations[geoname_id] = {
                    "continent_name": row.get("continent_name", "Unknown"),
                    "country_name": row.get("country_name", "Unknown"),
                    "city_name": row.get("city_name", "Unknown"),
                    "country_iso_code": row.get("country_iso_code"),
                    "continent_code": row.get("continent_code")
                }
    
    logger.info(f"Loaded {len(arabic_locations)} Arabic and {len(english_locations)} English location entries.")


load_location_labels()

def get_ip_version(ip_address: str) -> str:
    try:
        ip = ipaddress.ip_address(ip_address)
        return "IPv4" if isinstance(ip, ipaddress.IPv4Address) else "IPv6"
    except ValueError:
        return "Invalid IP Address"

def is_valid_ip(ip: str) -> bool:
    try:
        ipaddress.ip_address(ip.split(":")[0])
        return True
    except ValueError:
        return False

def find_geo(ip_address: str) -> dict:
    geoipdata = {
        "ip": ip_address,
        "ip_version": get_ip_version(ip_address),
        "generatedAt": datetime.datetime.now().isoformat()
    }
    try:
        reader = Reader(MMDB_OUTPUT)
        resp = reader.city(ip_address)

        # Country data
        if resp and resp.country:
            geoipdata["country"] = {
                "iso_code": resp.country.iso_code or "ZZ",
                "en": resp.country.names.get("en", "Unknown"),
                "ar": resp.country.names.get("ar", "غير معروف")
            }
        else:
            geoipdata["country"] = {
                "iso_code": "ZZ",
                "en": "Unknown",
                "ar": "غير معروف"
            }

        # Continent data
        if resp and resp.continent:

            geoipdata["continent"] = {
                "code": resp.continent.code or "XX",
                "en": resp.continent.names.get("en", "Unknown"),
                "ar": resp.continent.names.get("ar", "غير معروف")
            }
        else:
            geoipdata["continent"] = {
                "code": "XX",
                "en": "Unknown",
                "ar": "غير معروف"
            }

        # Location data

        if resp and resp.location:
            postal_code = getattr(resp.postal, "code", None) if hasattr(resp, "postal") else None
            geoipdata["location"] = {
                "latitude": resp.location.latitude,
                "longitude": resp.location.longitude,
                "postal_code": postal_code,
            }
            if resp.location.latitude and resp.location.longitude:
                geoipdata["map"] = f'https://www.google.com/maps/@{resp.location.latitude},{resp.location.longitude},15z'
            else:
                geoipdata["map"] = None
        else:
            geoipdata["location"] = {
                "latitude": None,
                "longitude": None,
                "postal_code": None
            }
            geoipdata["map"] = None

        # City data
        if resp and resp.city:
            geoipdata["city"] = {
                "en": resp.city.names.get("en", "Unknown"),
                "ar": resp.city.names.get("ar", "غير معروف")
            }
        else:
            geoipdata["city"] = None

        reader.close()
    except Exception as e:
        geoipdata["error"] = str(e)
    return geoipdata


@app.get("/ip")
async def get_my_ip(request: Request):
    ip = request.headers.get("CF-Connecting-IP") or request.client.host
    return {"your_ip": ip}


@app.get("/ip/{input_ip}")
async def get_geo_for_ip(input_ip: str):
    if is_valid_ip(input_ip):
        return find_geo(input_ip)
    return {"error": "Invalid IP address"}


@app.get("/ipall")
def ipall():
    """
    Return a list of the first 100 IP networks with full details in English and Arabic.
    """
    try:
        ip_details = []
        with open(BLOCKS_CSV, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                if count >= 100:
                    break
                network = row.get("network")
                city_id = str(row.get("geoname_id", "")).strip()
                country_id = str(row.get("registered_country_geoname_id", "")).strip()
                
                if network:
                    # Get Arabic names
                    ar_city = arabic_locations.get(city_id, {})
                    ar_country = arabic_locations.get(country_id, {})
                    
                    # Get English names and codes
                    en_city = english_locations.get(city_id, {})
                    en_country = english_locations.get(country_id, {})
                    
                    ip_details.append({
                        "network": network,
                        "country": {
                            "id": country_id,
                            "iso_code": ar_country.get("country_iso_code", "ZZ"),
                            "en": en_country.get("country_name", "Unknown"),
                            "ar": ar_country.get("country_name", "غير معروف")
                        },
                        "city": {
                            "id": city_id,
                            "en": en_city.get("city_name", "Unknown"),
                            "ar": ar_city.get("city_name", "غير معروف")
                        },
                        "continent": {
                            "code": ar_country.get("continent_code", "XX"),
                            "en": en_country.get("continent_name", "Unknown"),
                            "ar": ar_country.get("continent_name", "غير معروف")
                        }
                    })
                    count += 1
        return {"ip_networks": ip_details}
    except Exception as e:
        return {"error": str(e)}




@app.post("/geoip/rebuild")
def rebuild_mmdb():
    """
    Rebuild the MMDB database file from CSV blocks and Arabic labels.
    Enhanced with logging and detailed error messages.
    """
    try:
        writer = MMDBWriter(
            database_type="GeoLite2-City-Custom",
            languages=["en", "ar"],
            ip_version=4,
        )


        with open(BLOCKS_CSV, encoding="utf-8") as f:
            reader = csv.DictReader(f)

            count = 0
            errors = []
            for row in reader:
                network = row["network"]
                city_id = str(row["geoname_id"]).strip()
                country_id = str(row["registered_country_geoname_id"]).strip()
                if not country_id:
                    logger.warning(f"Skipping network {network} due to missing country_id")
                    continue

                # Log geoname_id presence for debugging
                #logger.info(f"Processing network {network} with city_id: {city_id}, country_id: {country_id}")
                if not city_id:
                    logger.warning(f"Missing city_id for network {network}")
                if not country_id:
                    logger.warning(f"Missing country_id for network {network}")

                ar_country = arabic_locations.get(country_id, {})
                ar_city = arabic_locations.get(city_id, {})

                # Get English names and codes
                en_city = english_locations.get(city_id, {})
                en_country = english_locations.get(country_id, {})

                record = {
                    "country": {
                        "id": country_id,
                        "names": {
                            "en": en_country.get("country_name", "Unknown"),
                            "ar": ar_country.get("country_name", "غير معروف")
                        },
                        "iso_code": ar_country.get("country_iso_code") or en_country.get("country_iso_code", "ZZ")
                    },
                    "city": {
                        "id": city_id,
                        "geoname_id": city_id,
                        "names": {
                            "en": en_city.get("city_name", "Unknown"),
                            "ar": ar_city.get("city_name", "غير معروف")
                        }
                    },
                    "continent": {
                        "names": {
                            "en": en_country.get("continent_name", "Unknown"),
                            "ar": ar_country.get("continent_name", "غير معروف")
                        },
                        "code": ar_country.get("continent_code") or en_country.get("continent_code", "XX")
                    },
                    "location": {
                        "latitude": str(row["latitude"]).strip(),
                        "longitude":  str(row["longitude"]).strip(),
                        "time_zone":  ar_country.get("time_zone") or en_country.get("time_zone", "Unknown"),
                        "postal_code":  str(row["postal_code"]).strip()
                    }
                }

                try:
                    writer.insert_network(IPSet([network]), record)
                    count += 1
                    #logger.info(f"Inserted network {network} with geoname_id {city_id}")
                    # if count > 5000 :
                    #     break  # Limit to first 1000 records for testing
                except Exception as e:
                    error_msg = f"⚠️ {network}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

        writer.to_db_file(MMDB_OUTPUT)
        logger.info(f"MMDB file rebuilt with {count} records.")

        if errors:
            return {
                "status": "partial_success",
                "message": f"MMDB file rebuilt with {count} records, but some errors occurred.",
                "errors": errors,
            }
        else:
            return {"status": "success", "message": f"MMDB file rebuilt with {count} records."}
    except Exception as e:
        logger.error(f"Error rebuilding MMDB: {e}")
        return {"status": "error", "message": str(e)}
