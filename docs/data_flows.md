# Data-flow and use-case drawing notes

## Context / Level 0 DFD

**System:** Virasat Django web application. **External entities:** anonymous visitor; buyer; artisan; verifier; site administrator; optional Anthropic Messages endpoint (only from `catalog/ai_service.py`). No payment gateway is present: UPI is a demo choice and cash on delivery is recorded, not processed online.

**Incoming flows:** visitors send search filters and product requests; buyers send registration/login, cart updates, checkout addresses, reviews, custom requests and proposal decisions; artisans send notes, product photos, edits, delivery updates and proposals; verifiers send approval/rejection; admin sends authorised admin edits; optional AI endpoint returns JSON draft text.

**Outgoing flows:** catalog pages, maker badges, safe error messages, cart/order details, plain-text VR invoices, request matches, offer decisions, dashboard figures and optional AI-assisted draft previews. The AI endpoint receives only the supplied craft, state, materials, technique, notes and language hint; it receives no buyer address, account password or API key in the user message. The API key is sent separately in the HTTP header by the server.

## Level 1 processes and data stores

1. **P1 Accounts and permissions** (`accounts/views.py`): credentials → Django User/Group and Profile; verified status → public badge. Only Verifier permission accesses approval actions. A session tracks login.
2. **P2 Catalog and AI** (`catalog/views.py`, `catalog/ai_service.py`): artisan facts and photo → validated draft Product → optional AI response or fallback → artisan edit → published Product. Product searches → published products; reviews and wishlists → buyer-only records. Recent IDs and language preference live in browser cookies.
3. **P3 Cart and orders** (`orders/cart.py`, `orders/views.py`): buyer product IDs and quantities → session cart → atomic stock check → Order and OrderItem snapshots. Cancellation restores Product stock; an invoice reads only the owning buyer's order.
4. **P4 Market linkage** (`linkage/views.py`, `linkage/matching.py`): buyer request → scored matches from artisan Product and Profile → proposal → buyer decision → accepted/rejected Proposal and closed BuyerRequest.
5. **P5 Reporting** (`core/views.py:impact`, `catalog/views.py:artisan_earnings`): published Products, verified Profiles, and delivered OrderItems → calculated public impact and private artisan amounts.

**D1** Django `auth_user` and `auth_group` plus `accounts_profile`; **D2** `catalog_category`, `catalog_crafttradition`, `catalog_product`, `catalog_review`, `catalog_wishlist`; **D3** Django `django_session` (`cart`, AI daily counter, login); **D4** `orders_order`, `orders_orderitem`; **D5** `linkage_buyerrequest`, `linkage_proposal`; **D6** uploaded and seed-generated image files in `media/`; **D7** event records in ignored `logs/app.log`. `lang` and `recently_viewed` are client-side cookies rather than database stores.

## Use-case diagram inputs

- **Visitor:** browse home/products/crafts/artisans/impact, choose English or Hindi, register, sign in.
- **Buyer:** manage profile, save and review delivered products, manage cart, check out, see own orders and invoice, cancel a placed item, post and close requests, accept or reject offers.
- **Artisan:** manage profile and products, generate/review drafts, publish/archive, fulfil own order items, browse matches and submit one offer per request.
- **Verifier:** inspect pending artisan profiles, approve or reject; the verifier is created in admin/seed, not public registration.
- **Administrator:** manage users, model records and permissions using Django Admin.
- **Optional AI provider:** return structured text; if unavailable, P2 continues offline.

**Trust boundaries:** forms use CSRF; role checks use session authentication and permissions; edit/order/request actions filter by owner in the database; the AI service never directly publishes products; invoices are restricted to the buyer. Draw datastore arrows only to processes that use them.
