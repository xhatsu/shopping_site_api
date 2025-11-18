#!/usr/bin/env bash
# Quick API endpoint tests using curl. Requires jq for JSON parsing.
# Usage: BASE_URL=http://localhost:5000 ./tests/api_endpoints_curl.sh

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:5000}"
CONTENT_TYPE="Content-Type: application/json"

# Helper to print sections
section() { printf "\n--- %s ---\n" "$1"; }

# Credentials (change if needed)
USERNAME="testuser"
EMAIL="testuser@example.com"
PASSWORD="testpass"

# 0) helper to extract token from JSON
extract_token() {
  echo "$1" | jq -r '.access_token // empty'
}

# 1) Try to login to get JWT token
section "Login user (attempt)"
LOGIN_PAYLOAD=$(jq -n --arg u "$USERNAME" --arg p "$PASSWORD" '{username:$u, password:$p}')
LOGIN_RESP=$(curl -s -X POST "$BASE_URL/api/auth/login" -H "$CONTENT_TYPE" -d "$LOGIN_PAYLOAD" || true)
TOKEN=$(extract_token "$LOGIN_RESP" || true)

if [[ -z "$TOKEN" || "$TOKEN" == "null" ]]; then
  section "Register user (because login returned no token)"
  REGISTER_PAYLOAD=$(jq -n --arg u "$USERNAME" --arg e "$EMAIL" --arg p "$PASSWORD" '{username:$u, email:$e, password:$p}')
  REGISTER_RESP=$(curl -s -X POST "$BASE_URL/api/auth/register" -H "$CONTENT_TYPE" -d "$REGISTER_PAYLOAD" || true)
  echo "$REGISTER_RESP" | jq .
  # Try login again to get token
  LOGIN_RESP=$(curl -s -X POST "$BASE_URL/api/auth/login" -H "$CONTENT_TYPE" -d "$LOGIN_PAYLOAD" || true)
  TOKEN=$(extract_token "$LOGIN_RESP" || true)
fi

if [[ -z "$TOKEN" || "$TOKEN" == "null" ]]; then
  echo "ERROR: failed to obtain access token from login/register."
  echo "Login response:"
  echo "$LOGIN_RESP" | jq .
  exit 1
fi

echo "Got token: ${TOKEN:0:20}... (truncated)"
AUTH_HEADER="Authorization: Bearer $TOKEN"

# 2) Products - list (paginated)
section "List products (page 1)"
curl -s -X GET "$BASE_URL/api/products?page=1&per_page=5" -H "$AUTH_HEADER" -H "$CONTENT_TYPE" | jq .

# 3) Products - create (protected)
section "Create product"
CREATE_PRODUCT_PAYLOAD='{"name":"Test Product","description":"Sample","price":9.99,"stock":10}'
PRODUCT_JSON=$(curl -s -X POST "$BASE_URL/api/products" -H "$CONTENT_TYPE" -H "$AUTH_HEADER" -d "$CREATE_PRODUCT_PAYLOAD")
echo "$PRODUCT_JSON" | jq .
PRODUCT_ID=$(echo "$PRODUCT_JSON" | jq -r '.product.id')
echo "PRODUCT_ID=$PRODUCT_ID"

# 4) Products - get single
section "Get product"
curl -s -X GET "$BASE_URL/api/products/$PRODUCT_ID" -H "$CONTENT_TYPE" | jq .

# 5) Products - update (protected)
section "Update product"
UPDATE_PRODUCT_PAYLOAD='{"price":12.5,"stock":20}'
curl -s -X PUT "$BASE_URL/api/products/$PRODUCT_ID" -H "$CONTENT_TYPE" -H "$AUTH_HEADER" -d "$UPDATE_PRODUCT_PAYLOAD" | jq .

# 6) Cart - get (protected)
section "Get cart (empty)"
curl -s -X GET "$BASE_URL/api/cart" -H "$CONTENT_TYPE" -H "$AUTH_HEADER" | jq .

# 7) Cart - add product (protected)
section "Add to cart"
ADD_CART_PAYLOAD=$(jq -n --arg pid "$PRODUCT_ID" --argjson qty 2 '{product_id: ($pid|tonumber), quantity: $qty}')
ADD_JSON=$(curl -s -X POST "$BASE_URL/api/cart/add" -H "$CONTENT_TYPE" -H "$AUTH_HEADER" -d "$ADD_CART_PAYLOAD")
echo "$ADD_JSON" | jq .
ITEM_ID=$(echo "$ADD_JSON" | jq -r '.item.id')
echo "ITEM_ID=$ITEM_ID"

# 8) Cart - get (now has item)
section "Get cart (with item)"
curl -s -X GET "$BASE_URL/api/cart" -H "$CONTENT_TYPE" -H "$AUTH_HEADER" | jq .

# 9) Cart - update item quantity (protected)
section "Update cart item"
UPDATE_ITEM_PAYLOAD='{"quantity":3}'
curl -s -X PUT "$BASE_URL/api/cart/item/$ITEM_ID" -H "$CONTENT_TYPE" -H "$AUTH_HEADER" -d "$UPDATE_ITEM_PAYLOAD" | jq .

# 10) Cart - remove specific item (protected)
section "Remove cart item"
curl -s -X DELETE "$BASE_URL/api/cart/item/$ITEM_ID" -H "$CONTENT_TYPE" -H "$AUTH_HEADER" | jq .

# 11) Cart - add again then clear (protected)
section "Add then clear cart"
ADD_JSON2=$(curl -s -X POST "$BASE_URL/api/cart/add" -H "$CONTENT_TYPE" -H "$AUTH_HEADER" -d "$ADD_CART_PAYLOAD")
echo "$ADD_JSON2" | jq .
curl -s -X DELETE "$BASE_URL/api/cart/clear" -H "$CONTENT_TYPE" -H "$AUTH_HEADER" | jq .

# 12) Products - delete created product (protected)
section "Delete product"
curl -s -X DELETE "$BASE_URL/api/products/$PRODUCT_ID" -H "$CONTENT_TYPE" -H "$AUTH_HEADER" | jq .

section "Done"
