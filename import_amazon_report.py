#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Affilimax - Import du rapport de revenus Amazon Partenaires
============================================================
Amazon ne fournit PAS de webhook temps reel : il met a jour un rapport CSV
1-2 fois par jour sur partenaires.amazon.fr. Ce script lit ce rapport et
envoie chaque vente au webhook /amazon/notification (qui credite les stats
et le solde du bon partenaire via ?ref / tracking id).

Utilisation :
    python import_amazon_report.py rapport_ventes.csv
    python import_amazon_report.py rapport_ventes.csv --dry-run      # test sans rien crediter
    python import_amazon_report.py rapport_ventes.csv --webhook http://localhost:8765/amazon/notification
    python import_amazon_report.py rapport_ventes.csv --secret MA_CLE

Par defaut : webhook = https://afflimax.onrender.com/amazon/notification
et secret = variable d'env AMAZON_WEBHOOK_SECRET (ou --secret).
"""

import argparse
import csv
import json
import os
import sys
import urllib.request

DEFAULT_WEBHOOK = os.environ.get(
    "AMAZON_WEBHOOK_URL",
    "https://afflimax.onrender.com/amazon/notification",
)

# Mapping flexible des noms de colonnes Amazon (plusieurs formats possibles)
COL_ORDER_ID = ("order id", "order_id", "orderid", "transaction id", "transactionid")
COL_PRODUCT = ("item name", "product title", "product", "item", "title", "produit")
COL_COMMISSION = ("referral fee", "commission", "fee", "commissions", "montant")
COL_PRICE = ("item price", "price", "prix", "total", "amount")
COL_QTY = ("quantity", "qty", "item quantity", "itemquantity")
COL_ASIN = ("asin", "asin/isbn", "asin / isbn", "itemid")
COL_TRACKING = ("tracking id", "trackingid", "tag", "ref")


def find_col(headers, candidates):
    """Retourne l'index de la premiere colonne dont le nom matche."""
    low = [h.strip().lower() for h in headers]
    for c in candidates:
        for i, h in enumerate(low):
            if h == c:
                return i
    # Second pass : correspondance partielle (ex: "Order ID" vs "order-id")
    for c in candidates:
        for i, h in enumerate(low):
            if c.replace(" ", "") in h.replace(" ", "").replace("_", "-"):
                return i
    return None


def parse_float(v):
    if v is None:
        return None
    try:
        s = str(v).replace("EUR", "").replace("€", "").replace(" ", "").replace(",", ".").strip()
        return round(float(s), 2) if s else None
    except Exception:
        return None


def read_report(path):
    """Lit le CSV Amazon et retourne la liste des ventes (dict normalise)."""
    sales = []
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            print("Fichier vide.")
            return []
        headers = [h.strip() for h in headers]

        i_order = find_col(headers, COL_ORDER_ID)
        i_prod = find_col(headers, COL_PRODUCT)
        i_comm = find_col(headers, COL_COMMISSION)
        i_price = find_col(headers, COL_PRICE)
        i_qty = find_col(headers, COL_QTY)
        i_asin = find_col(headers, COL_ASIN)
        i_track = find_col(headers, COL_TRACKING)

        print(f"Colonnes detectees: order_id={i_order} produit={i_prod} "
              f"commission={i_comm} prix={i_price} qte={i_qty} asin={i_asin} tracking={i_track}")

        for row in reader:
            if not row or not any(c.strip() for c in row):
                continue
            def g(idx):
                return row[idx].strip() if idx is not None and idx < len(row) else ""

            order_id = g(i_order)
            product = g(i_prod)
            commission = parse_float(g(i_comm))
            price = parse_float(g(i_price))
            qty = 1
            try:
                qty = max(1, int(float(g(i_qty)))) if g(i_qty) else 1
            except Exception:
                qty = 1
            asin = g(i_asin)
            tracking = g(i_track)

            # Ne garder que les lignes de ventes valides
            if not order_id and not product:
                continue
            # Lignes d'agregat (ex: "Total", "Sous-total") : jamais une vente
            product_low = product.strip().lower()
            if product_low in ("total", "sous-total", "subtotal", "total general",
                               "total des revenus", "grand total"):
                continue
            # Lignes d'agregat (ex: "Total") sans order id reel
            if not order_id and i_order is not None:
                continue
            # Une vraie vente a toujours un order id OU un produit nomme
            if not order_id and not product:
                continue
            # IMPORTANT : le rapport Amazon donne deja le Referral Fee TOTAL de
            # la ligne (quantite incluse). On envoie donc quantity=1 pour eviter
            # que le webhook remultiplie la commission par la quantite (double
            # comptage verifie par test).
            sales.append({
                "orderId": order_id,
                "productTitle": product,
                "commission": commission,
                "price": price,
                "quantity": 1,
                "asin": asin,
                "ref": tracking,
            })
    return sales


def send_sale(sale, webhook, secret, dry_run=False):
    """Envoie une vente au webhook. Retourne le statut."""
    payload = {k: v for k, v in sale.items() if v is not None and v != ""}
    body = json.dumps(payload).encode("utf-8")
    if dry_run:
        return f"[DRY-RUN] {payload.get('productTitle', '?')} | comm={payload.get('commission')} | order={payload.get('orderId')}"
    req = urllib.request.Request(webhook, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    if secret:
        req.add_header("X-Amzn-Webhook-Secret", secret)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("status") == "ok":
                if result.get("duplicate"):
                    return f"DOUBLON ignore (deja comptee) | order={payload.get('orderId')}"
                return f"OK {payload.get('productTitle', '?')[:40]} | comm={payload.get('commission')} EUR | order={payload.get('orderId')}"
            return f"IGNORE {result.get('message', '?')} | {payload.get('productTitle', '?')[:40]}"
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")[:120]
        return f"HTTP {e.code} | {detail}"
    except Exception as e:
        return f"ERREUR {e}"


def main():
    ap = argparse.ArgumentParser(description="Import des ventes Amazon Partenaires")
    ap.add_argument("csv", help="Chemin du rapport CSV telecharge depuis partenaires.amazon.fr")
    ap.add_argument("--webhook", default=DEFAULT_WEBHOOK, help="URL du webhook (defaut: Render)")
    ap.add_argument("--secret", default=os.environ.get("AMAZON_WEBHOOK_SECRET", ""),
                    help="Secret webhook (defaut: env AMAZON_WEBHOOK_SECRET)")
    ap.add_argument("--dry-run", action="store_true", help="Affiche ce qui serait importe sans crediter")
    args = ap.parse_args()

    if not os.path.exists(args.csv):
        print(f"Fichier introuvable: {args.csv}")
        sys.exit(1)

    sales = read_report(args.csv)
    print(f"\n{len(sales)} ventes trouvees dans le rapport")
    if not sales:
        sys.exit(0)

    # Statistiques
    total_comm = sum(s["commission"] for s in sales if s["commission"])
    print(f"Commission totale du rapport: {round(total_comm, 2)} EUR")

    ok = ignored = errors = 0
    for i, sale in enumerate(sales, 1):
        res = send_sale(sale, args.webhook, args.secret, dry_run=args.dry_run)
        if res.startswith("OK"):
            ok += 1
        elif res.startswith("DOUBLON") or res.startswith("IGNORE"):
            ignored += 1
        else:
            errors += 1
        print(f"  {i}. {res}")
    if args.dry_run:
        print("\n(DRY-RUN: aucune vente creditee)")
        return

    print(f"\n=== RESULTAT ===\nCreditees: {ok} | Deja vues/ignorees: {ignored} | Erreurs: {errors}")
    if errors:
        print("-> Verifie le secret webhook (--secret) et que AMAZON_WEBHOOK_SECRET est configure sur Render.")
    print("\nVerifie le dashboard: https://afflimax.onrender.com/dashboard")


if __name__ == "__main__":
    main()
