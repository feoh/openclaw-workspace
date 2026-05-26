#!/home/feoh/.openclaw/workspace/.venv/bin/python3
"""Generate a direct Speckled Ax add-to-cart link for Chris's preferred coffee.

Default target:
- Product: Map 40 Mokha Java
- Weight: 5 lbs

This intentionally stops short of fully automated checkout. Speckled Ax's account login
currently uses reCAPTCHA, so unattended account login/order submission would be brittle
and likely blocked. The generated link adds the item to the cart in the browser session
that opens it, where the existing user account can then be used normally.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass

PRODUCT_URL = "https://speckledax.com/product/map-40-mokha-java/"
EXPECTED_PRODUCT_ID = 86
EXPECTED_WEIGHT = "5 lbs"
EXPECTED_VARIATION_ID = 125


@dataclass
class ProductChoice:
    product_id: int
    variation_id: int
    attribute_name: str
    attribute_value: str
    product_url: str

    def add_to_cart_url(self) -> str:
        params = {
            "add-to-cart": str(self.product_id),
            "variation_id": str(self.variation_id),
            self.attribute_name: self.attribute_value,
        }
        return f"https://speckledax.com/?{urllib.parse.urlencode(params)}"


class SpeckledAxError(RuntimeError):
    pass


def fetch_choice(product_url: str, desired_weight: str) -> ProductChoice:
    with urllib.request.urlopen(product_url, timeout=30) as resp:
        page = resp.read().decode("utf-8", errors="ignore")

    product_match = re.search(r'data-product_id="(\d+)"', page)
    variations_match = re.search(r'data-product_variations="([^"]+)"', page)
    if not product_match or not variations_match:
        raise SpeckledAxError("Could not find WooCommerce product metadata on the page")

    product_id = int(product_match.group(1))
    variations = json.loads(html.unescape(variations_match.group(1)))

    for variation in variations:
        attrs = variation.get("attributes", {})
        for attr_name, attr_value in attrs.items():
            if attr_value == desired_weight:
                return ProductChoice(
                    product_id=product_id,
                    variation_id=int(variation["variation_id"]),
                    attribute_name=attr_name,
                    attribute_value=attr_value,
                    product_url=product_url,
                )

    raise SpeckledAxError(f"Could not find a variation for weight {desired_weight!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Speckled Ax add-to-cart link")
    parser.add_argument("--weight", default=EXPECTED_WEIGHT, help="Desired weight, default: 5 lbs")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON")
    parser.add_argument("--verify-live", action="store_true", help="Fetch live product metadata before generating the link")
    args = parser.parse_args()

    if args.verify_live:
        choice = fetch_choice(PRODUCT_URL, args.weight)
    else:
        choice = ProductChoice(
            product_id=EXPECTED_PRODUCT_ID,
            variation_id=EXPECTED_VARIATION_ID,
            attribute_name="attribute_weight",
            attribute_value=args.weight,
            product_url=PRODUCT_URL,
        )

    payload = {
        "product": "Map 40 Mokha Java",
        "weight": choice.attribute_value,
        "product_id": choice.product_id,
        "variation_id": choice.variation_id,
        "product_url": choice.product_url,
        "add_to_cart_url": choice.add_to_cart_url(),
        "note": "Open the add_to_cart_url in your browser to add the coffee to your cart, then check out with your Speckled Ax account.",
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Product: {payload['product']}")
        print(f"Weight: {payload['weight']}")
        print(f"Add to cart: {payload['add_to_cart_url']}")
        print(payload["note"])
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SpeckledAxError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
