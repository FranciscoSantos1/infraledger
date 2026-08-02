"""
Pricing service — wraps the AWS Pricing API via boto3.
See docs/architecture.md -> Cost Calculation Flow.
"""
import json
from datetime import datetime, timedelta

import boto3
from flask import current_app

from app.extensions import db
from models.price_cache import PriceCache
from models.cost_entry import CostEntry

# The Pricing API's EC2 filters require the human-readable region name,
# not the region code — a genuine AWS API inconsistency, not a design choice.

HOURS_PER_MONTH = 730

REGION_CODE_TO_LOCATION = {
    "eu-west-1": "EU (Ireland)",
    "eu-west-2": "EU (London)",
    "eu-west-3": "EU (Paris)",
    "eu-central-1": "EU (Frankfurt)",
    "us-east-1": "US East (N. Virginia)",
    "us-west-2": "US West (Oregon)",
}

_pricing_client = boto3.client("pricing", region_name="us-east-1")

def _extract_on_demand_price(price_list_item):
    """
    Given one raw PriceList item (already json.loads'd), pull out the
    on-demand hourly price. Returns (price_per_unit: float, unit: str)
    """

    on_demand_terms = price_list_item["terms"]["OnDemand"]
    term_key = next(iter(on_demand_terms))
    price_dimensions = on_demand_terms[term_key]["priceDimensions"]
    dimension_key = next(iter(price_dimensions))
    dimension = price_dimensions[dimension_key]

    price_per_unit = float(dimension["pricePerUnit"]["USD"])
    unit = dimension["unit"]
    return price_per_unit, unit

def fetch_price_from_aws(service_code: str, sku: str, region:str):
    """Calls the AWS Pricing API for EC2 on-demand Linux pricing and
    stores the result in PriceCache. Returns the PriceCache row."""

    location = REGION_CODE_TO_LOCATION.get(region)
    if location is None:
        raise ValueError(f"No location mapping for region '{region}' — add it to REGION_CODE_TO_LOCATION")

    response = _pricing_client.get_products(
        ServiceCode = service_code,
        Filters=[
            {"Type": "TERM_MATCH", "Field": "instanceType", "Value": sku},
            {"Type": "TERM_MATCH", "Field": "location", "Value": location},
            {"Type": "TERM_MATCH", "Field": "operatingSystem", "Value": "Linux"},
            {"Type": "TERM_MATCH", "Field": "tenancy", "Value": "Shared"},
            {"Type": "TERM_MATCH", "Field": "preInstalledSw", "Value": "NA"},
            {"Type": "TERM_MATCH", "Field": "capacitystatus", "Value": "Used"},
        ],
        MaxResults=1,
    )

    if not response["PriceList"]:
        raise ValueError(f"No pricing found for {service_code}/{sku}/{region}")

    price_item = json.loads(response["PriceList"][0])
    price_per_unit, unit = _extract_on_demand_price(price_item)

    cache_entry = PriceCache.query.filter_by(
        service_code=service_code, sku=sku, region=region
    ).first()

    if cache_entry is None:
        cache_entry = PriceCache(service_code=service_code, sku=sku, region=region)
        db.session.add(cache_entry)

    cache_entry.price_per_unit = price_per_unit
    cache_entry.unit = unit
    cache_entry.fetched_at = datetime.utcnow()

    db.session.commit()
    return cache_entry

def get_price(service_code: str, sku: str, region: str):
    """Cache-first price lookup. Returns a PriceCache row — fresh from
    cache if available, otherwise fetched live from AWS."""

    ttl_hours = current_app.config["PRICE_CACHE_TTL_HOURS"]
    cutoff = datetime.utcnow() - timedelta(hours=ttl_hours)

    cache_entry = PriceCache.query.filter_by(
        service_code=service_code, sku=sku, region=region
    ).first()

    if cache_entry is not None and cache_entry.fetched_at >= cutoff:
        return cache_entry

    return fetch_price_from_aws(service_code, sku, region)

def calculate_monthly_cost(resource):
    """
    Given a Resource, fetch/ cache its price and create a CostEntry
    """
    # k8s_node is priced identically to ec2 — same underlying instance type,
    
    service_code_map = {
        "ec2": "AmazonEC2",
        "k8s_node": "AmazonEC2",
    }
    service_code = service_code_map.get(resource.type)
    if service_code is None:
        raise ValueError(f"No pricing support yet for resource type '{resource.type}'")

    price = get_price(service_code, resource.provider_sku, resource.provider_region)

    if price.unit != "Hrs":
        raise ValueError(f"Unexpected pricing unit '{price.unit}' — only hourly pricing is handled so far")

    monthly_cost = price.price_per_unit * HOURS_PER_MONTH

    cost_entry = CostEntry(
        resource_id=resource.id,
        estimated_monthly_cost=round(monthly_cost, 2),
        currency="USD",
    )
    db.session.add(cost_entry)
    db.session.commit()
    return cost_entry

