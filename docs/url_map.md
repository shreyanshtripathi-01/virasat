# Named URL map

Routes are declared in `core/urls.py`, `accounts/urls.py`, `catalog/urls.py`, `orders/urls.py`, `linkage/urls.py` and included in `virasat/urls.py`. `<id>` below means an integer `pk`. `GET/POST` means the same view renders on GET and validates on POST; successful writes redirect. Unauthorised guests are redirected to `/accounts/login/?next=...`; a signed-in user without the required role sees the custom 403. POST forms include CSRF tokens.

| Route | Name | View | Methods | Access and rule |
| --- | --- | --- | --- | --- |
| `/` | `core:home` | `core.views.home` | GET | Public |
| `/about/` | `core:about` | `core.views.about` | GET | Public |
| `/impact/` | `core:impact` | `core.views.impact` | GET | Public |
| `/manifest.webmanifest` | `core:manifest` | `core.views.manifest` | GET | Public; PWA extension |
| `/sw.js` | `core:service_worker` | `core.views.service_worker` | GET | Public; PWA extension; root scope header |
| `/offline/` | `core:offline` | `core.views.offline` | GET | Public; PWA extension |
| `/language/<en\|hi>/` | `core:language` | `core.views.change_language` | GET | Public; sets language cookie; regex |
| `/accounts/register/` | `accounts:register` | `accounts.views.register` | GET/POST | Guest; only artisan/buyer roles |
| `/accounts/login/` | `accounts:login` | `accounts.views.login_view` | GET/POST | Guest; safe `next` |
| `/accounts/logout/` | `accounts:logout` | `accounts.views.logout_view` | POST | Public POST; signs out the current session |
| `/accounts/profile/` | `accounts:profile` | `accounts.views.profile` | GET | Login; own profile |
| `/accounts/profile/edit/` | `accounts:profile_edit` | `accounts.views.edit_profile` | GET/POST | Login; own profile |
| `/artisans/<id>/` | `accounts:artisan_detail` | `accounts.views.artisan_detail` | GET | Public; artisan's published products |
| `/accounts/verify/` | `accounts:verification_queue` | `accounts.views.verification_queue` | GET | Login + `accounts.can_verify_artisan` |
| `/accounts/verify/<id>/approve/` | `accounts:approve` | `accounts.views.approve_artisan` | POST | Verifier permission; pending artisan |
| `/accounts/verify/<id>/reject/` | `accounts:reject` | `accounts.views.reject_artisan` | POST | Verifier permission; pending artisan |
| `/products/` | `catalog:product_list` | `catalog.views.product_list` | GET | Public; filter, sort, paginate |
| `/product/<id>/<slug>/` | `catalog:product_detail` | `catalog.views.product_detail` | GET | Public published; draft owner only; regex |
| `/craft/<slug>/` | `catalog:craft_detail` | `catalog.views.craft_detail` | GET | Public |
| `/category/<slug>/` | `catalog:category_detail` | `catalog.views.category_detail` | GET | Public |
| `/wishlist/` | `catalog:wishlist` | `catalog.views.wishlist` | GET | Buyer only |
| `/wishlist/toggle/<id>/` | `catalog:wishlist_toggle` | `catalog.views.toggle_wishlist` | POST | Buyer; published product |
| `/product/<id>/review/` | `catalog:review` | `catalog.views.submit_review` | POST | Buyer; delivered item; one review per buyer/product |
| `/dashboard/` | `catalog:dashboard` | `catalog.views.artisan_dashboard` | GET | Artisan only |
| `/dashboard/products/` | `catalog:artisan_products` | `catalog.views.artisan_products` | GET | Artisan; own listings |
| `/dashboard/products/new/` | `catalog:product_new` | `catalog.views.new_product` | GET | Artisan; raw-notes form |
| `/dashboard/products/generate/` | `catalog:product_generate` | `catalog.views.generate_product` | POST | Artisan; creates private draft |
| `/dashboard/products/<id>/edit/` | `catalog:product_edit` | `catalog.views.edit_product` | GET/POST | Artisan owner; save/publish |
| `/dashboard/products/<id>/regenerate/` | `catalog:product_regenerate` | `catalog.views.regenerate_product` | POST | Artisan owner; confirmed; returns to draft |
| `/dashboard/products/<id>/status/` | `catalog:product_status` | `catalog.views.change_product_status` | POST | Artisan owner; draft/published/archived |
| `/dashboard/products/<id>/delete/` | `catalog:product_delete` | `catalog.views.delete_product` | GET/POST | Artisan owner; GET confirms, POST deletes when no order items |
| `/cart/` | `orders:cart` | `orders.views.cart_page` | GET | Buyer; session cart |
| `/cart/add/<id>/` | `orders:cart_add` | `orders.views.cart_add` | POST | Buyer; published item, stock cap |
| `/cart/update/<id>/` | `orders:cart_update` | `orders.views.cart_update` | POST | Buyer; stock cap |
| `/cart/remove/<id>/` | `orders:cart_remove` | `orders.views.cart_remove` | POST | Buyer; session only |
| `/checkout/` | `orders:checkout` | `orders.views.checkout` | GET/POST | Buyer; atomic checkout |
| `/orders/` | `orders:order_list` | `orders.views.buyer_orders` | GET | Buyer; own orders |
| `/orders/VR<6 digits>/` | `orders:order_detail` | `orders.views.order_detail` | GET | Buyer owner; regex |
| `/orders/VR<6 digits>/invoice/` | `orders:invoice` | `orders.views.invoice` | GET | Buyer owner; text attachment; regex |
| `/orders/items/<id>/cancel/` | `orders:cancel_item` | `orders.views.cancel_item` | POST | Buyer owner; only placed item |
| `/dashboard/orders/` | `orders:artisan_orders` | `orders.views.artisan_orders` | GET | Artisan; own order items |
| `/dashboard/orders/items/<id>/status/` | `orders:item_status` | `orders.views.update_item_status` | POST | Artisan owner; forward stage only |
| `/requests/` | `linkage:request_list` | `linkage.views.request_list` | GET | Login; open requests |
| `/requests/matches/` | `linkage:matched_requests` | `linkage.views.matched_requests` | GET | Artisan; scored open matches |
| `/requests/new/` | `linkage:request_new` | `linkage.views.new_request` | GET/POST | Buyer; own new request |
| `/requests/mine/` | `linkage:my_requests` | `linkage.views.my_requests` | GET | Buyer; own requests |
| `/requests/<id>/` | `linkage:request_detail` | `linkage.views.request_detail` | GET | Login; open public to logged-in; closed owner/proposer only |
| `/requests/<id>/propose/` | `linkage:propose` | `linkage.views.propose` | GET/POST | Artisan; one offer per open request |
| `/requests/<id>/close/` | `linkage:close_request` | `linkage.views.close_request` | POST | Buyer owner; open request |
| `/proposals/mine/` | `linkage:my_proposals` | `linkage.views.my_proposals` | GET | Artisan; own offers |
| `/proposals/<id>/accept/` | `linkage:accept_proposal` | `linkage.views.accept_proposal` | POST | Buyer owner; pending offer |
| `/proposals/<id>/reject/` | `linkage:reject_proposal` | `linkage.views.reject_proposal` | POST | Buyer owner; pending offer |

`/admin/` is Django Admin's own URL set, not a custom function-based view; staff permissions control it. In development with `DEBUG=True`, `/media/` serves uploaded images (`virasat/urls.py`). Root `handler400`, `handler403`, `handler404`, `handler500` point to function-based views in `core/views.py`. An invalid CSRF token uses `core.views.csrf_failure` from `virasat/settings.py`.
