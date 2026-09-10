#!/usr/bin/env python3
"""Sqlantra golden-set evaluation: rule-based vs LLM text-to-SQL.

Measures exact-match, semantic equivalence (executes + equal result rows),
median latency, and token cost over a 30-query hand-labeled set.

LLM path uses OpenRouter when OPENROUTER_API_KEY is set and
OLLAMA_URL (local) otherwise. Never prints credentials.
"""

import json
import os
import statistics
import time
import urllib.request
import urllib.error

from text_to_sql import rule_based_sql as rule_gen
from sqlantra_database_v2 import init_database, query_sql

DB_INIT = "/tmp/sqlantra_v2_demo.db"
llm_fallback_count = 0

DEFAULT_OPENROUTER_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
OPENROUTER_FALLBACK_MODELS = [
    "nvidia/nemotron-3-super-120b-a12b:free",
    "nvidia/nemotron-3.5-lightning:free",
    "google/gemma-4-26b-a4b-it:free",
    "google/gemma-4-31b-it:free",
]

# intent labels: RULE_OK  = rule engine has an exact pattern
#                RULE_NEAR = rule engine approximates only
#                LLM_ONLY = rule engine cannot express this intent
GOLDEN = [
    # --- class A: exact rule hits ---
    {"q": "Show all completed orders", "sql": "SELECT * FROM orders WHERE status = 'completed'", "cls": "RULE_OK"},
    {"q": "List every completed order", "sql": "SELECT * FROM orders WHERE status = 'completed'", "cls": "RULE_OK"},
    {"q": "Which orders are completed", "sql": "SELECT * FROM orders WHERE status = 'completed'", "cls": "RULE_OK"},
    {"q": "Show all pending orders", "sql": "SELECT * FROM orders WHERE status = 'pending'", "cls": "RULE_OK"},
    {"q": "List pending orders", "sql": "SELECT * FROM orders WHERE status = 'pending'", "cls": "RULE_OK"},
    {"q": "Show the daily sales report", "sql": "SELECT * FROM gold_daily_sales ORDER BY date DESC", "cls": "RULE_OK"},
    {"q": "Sales report by day", "sql": "SELECT * FROM gold_daily_sales ORDER BY date DESC", "cls": "RULE_OK"},
    {"q": "Show product performance", "sql": "SELECT * FROM gold_product_performance ORDER BY total_revenue DESC", "cls": "RULE_OK"},
    {"q": "Top products by revenue", "sql": "SELECT * FROM gold_product_performance ORDER BY total_revenue DESC", "cls": "RULE_OK"},
    {"q": "Show customer 360 summary", "sql": "SELECT * FROM gold_customer_360 ORDER BY total_spent DESC", "cls": "RULE_OK"},
    {"q": "Which orders are over 1000", "sql": "SELECT * FROM orders WHERE total_amount > 1000", "cls": "RULE_OK"},
    {"q": "Show orders over 500 dollars", "sql": "SELECT * FROM orders WHERE total_amount > 500", "cls": "RULE_OK"},
    # --- class B: rule approximates but output differs ---
    {"q": "Show me all products", "sql": "SELECT * FROM products", "cls": "RULE_NEAR"},
    {"q": "List the products we sell", "sql": "SELECT * FROM products", "cls": "RULE_NEAR"},
    {"q": "What is the total revenue today", "sql": "SELECT * FROM gold_daily_sales ORDER BY date DESC", "cls": "RULE_NEAR"},
    {"q": "Show me recent customer segments", "sql": "SELECT * FROM gold_customer_360 ORDER BY total_spent DESC", "cls": "RULE_NEAR"},
    {"q": "Get the customers table", "sql": "SELECT * FROM gold_customer_360 ORDER BY total_spent DESC", "cls": "RULE_NEAR"},
    {"q": "Show the sales data", "sql": "SELECT * FROM gold_daily_sales ORDER BY date DESC", "cls": "RULE_NEAR"},
    # --- class C: rule engine cannot express ---
    {"q": "Show cancelled orders", "sql": "SELECT * FROM orders WHERE status = 'cancelled'", "cls": "LLM_ONLY"},
    {"q": "How many cancelled orders are there", "sql": "SELECT COUNT(*) as cnt FROM orders WHERE status = 'cancelled'", "cls": "LLM_ONLY"},
    {"q": "List orders from the Web channel", "sql": "SELECT * FROM orders WHERE channel = 'Web'", "cls": "LLM_ONLY"},
    {"q": "Show orders placed on the App", "sql": "SELECT * FROM orders WHERE channel = 'App'", "cls": "LLM_ONLY"},
    {"q": "What is the total revenue of completed orders", "sql": "SELECT SUM(total_amount) as total_revenue FROM orders WHERE status = 'completed'", "cls": "LLM_ONLY"},
    {"q": "Show average order value", "sql": "SELECT AVG(total_amount) as avg_order_value FROM orders", "cls": "LLM_ONLY"},
    {"q": "What is the most expensive order", "sql": "SELECT * FROM orders ORDER BY total_amount DESC LIMIT 1", "cls": "LLM_ONLY"},
    {"q": "How many orders exist in total", "sql": "SELECT COUNT(*) as total_orders FROM orders", "cls": "LLM_ONLY"},
    {"q": "Show orders that joined products with their names", "sql": "SELECT o.order_id, o.order_date, o.total_amount, p.name FROM orders o JOIN order_items oi ON o.order_id = oi.order_id JOIN products p ON oi.product_id = p.product_id ORDER BY o.order_date DESC", "cls": "LLM_ONLY"},
    {"q": "List products with low stock", "sql": "SELECT * FROM products WHERE stock < 10 ORDER BY stock ASC", "cls": "LLM_ONLY"},
    {"q": "Show pending approvals", "sql": "SELECT * FROM hitl_approvals WHERE status = 'pending'", "cls": "LLM_ONLY"},
    {"q": "Total revenue grouped by channel", "sql": "SELECT channel, SUM(total_amount) as total FROM orders GROUP BY channel", "cls": "LLM_ONLY"},
]


def normalize(sql: str) -> str:
    s = sql.strip().rstrip(";").lower()
    return " ".join(s.split())


def snapshot_of(sql: str):
    res = query_sql(sql)
    if res.get("error"):
        return None
    cols = res.get("columns") or []
    sortme = []
    for row in res.get("data") or []:
        sortme.append(tuple(row.get(c) for c in cols))
    return frozenset(sorted(sortme, key=str)), tuple(cols)


def semantic_equal(generated: str, golden: str) -> bool:
    norm_g = normalize(generated) == normalize(golden)
    if norm_g:
        return True
    snap_g = snapshot_of(generated)
    snap_k = snapshot_of(golden)
    if snap_g is None or snap_k is None:
        return False
    return snap_g[0] == snap_k[0]


def run_llm(query: str, base_url: str, models: list) -> str:
    prompt = (
        "You are a text-to-SQL assistant for SQLite. Tables: "
        "orders(order_id, channel, customer_id, order_date, total_amount, status), "
        "products(product_id, name, category, price, stock), "
        "order_items(item_id, order_id, product_id, quantity, unit_price), "
        "gold_daily_sales(id, date, channel, total_orders, total_revenue, avg_order_value), "
        "gold_product_performance(id, product_id, product_name, category, total_sold, total_revenue, stock_alert), "
        "gold_customer_360(id, customer_id, total_orders, total_spent, avg_order_value, customer_segment, clv_prediction), "
        "hitl_approvals(approval_id, action_type, details, requester, status, comment). "
        "Return ONLY one SELECT statement, no explanation.\n"
        f"Question: {query}\nSQL:"
    )
    if base_url.endswith("api/generate"):
        model = models[0]
        body = {
            "model": model, "prompt": prompt, "stream": False,
            "options": {"temperature": 0.1, "num_predict": 256},
        }
    else:  # OpenRouter chat completions
        model = models[0]
        body = {
            "model": model, "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 256, "temperature": 0.1,
        }
    req = urllib.request.Request(
        base_url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            **({"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"} if base_url.startswith("https://openrouter") else {}),
        },
    )
    retries = 4
    last_err = None
    for candidate in models:
        if base_url.startswith("https://openrouter"):
            req = urllib.request.Request(
                base_url, data=json.dumps({**body, "model": candidate}).encode("utf-8"),
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"},
            )
        for attempt in range(retries):
            try:
                with urllib.request.urlopen(req, timeout=180) as resp:
                    out = json.loads(resp.read().decode())
                    if base_url.endswith("api/generate"):
                        return out.get("response", "")
                    return out["choices"][0]["message"]["content"]
            except urllib.error.HTTPError as e:
                last_err = e
                if e.code == 429:
                    time.sleep(3 * (attempt + 1))
                    continue
                break
            except Exception as e:
                last_err = e
                time.sleep(2) if attempt < retries - 1 else None
    raise last_err


def evaluate_path(gen_fn, label: str):
    exact = valid = sem = 0
    lats, tokens = [], 0
    rows = []
    for idx, item in enumerate(GOLDEN):
        q, golden = item["q"], item["sql"]
        t0 = time.time()
        sql = gen_fn(q)
        lat_ms = (time.time() - t0) * 1000
        lats.append(lat_ms)
        ex = normalize(sql) == normalize(golden)
        res = query_sql(sql)
        ok = res.get("error") is None
        se = semantic_equal(sql, golden)
        if ex:
            exact += 1
        if ok:
            valid += 1
        if se:
            sem += 1
        rows.append({"q": q, "sql": sql, "exact": ex, "valid": ok, "sem": se, "ms": lat_ms})
        if "LLM" in label and os.environ.get("OPENROUTER_API_KEY"):
            time.sleep(1.2)
    n = len(GOLDEN)
    return {
        "label": label,
        "n": n,
        "exact": exact, "valid": valid, "sem": sem,
        "exact_pct": 100 * exact / n,
        "valid_pct": 100 * valid / n,
        "sem_pct": 100 * sem / n,
        "lat_med": statistics.median(lats),
        "rows": rows,
    }


def main():
    init_database()
    runs = int(os.environ.get("EVAL_LLM_RUNS", "1"))
    print(f"Golden set: {len(GOLDEN)} queries | classes: "
          f"RULE_OK={sum(1 for g in GOLDEN if g['cls']=='RULE_OK')}, "
          f"RULE_NEAR={sum(1 for g in GOLDEN if g['cls']=='RULE_NEAR')}, "
          f"LLM_ONLY={sum(1 for g in GOLDEN if g['cls']=='LLM_ONLY')}")

    results = [evaluate_path(rule_gen, "rule_based_sql")]

    if run := _llm_config():
        url, model = run
        model_name = "openrouter:" + "/".join(model[0].split("/")[-2:]) if "openrouter" in url else model[0]
        agg = []
        for i in range(runs):
            t0 = time.monotonic()
            agg.append(evaluate_path(lambda q, u=url, m=model, r=rule_gen: _llm_guard(q, u, m, r), f"LLM ({model_name})"))
            print(f"run {i+1}/{runs}: exact={agg[-1]['exact']}/{agg[-1]['n']} equiv={agg[-1]['sem']} lat_med={agg[-1]['lat_med']:.0f}ms fallbacks={llm_fallback_count} ({time.monotonic()-t0:.0f}s)")
            if i < runs - 1 and "openrouter" in url:
                time.sleep(3)
        base = agg[0]
        llm_med = statistics.median(r["lat_med"] for r in agg)
        base["exact_pct"] = 100 * base["exact"] / base["n"]
        base["valid_pct"] = 100 * base["valid"] / base["n"]
        base["sem_pct"] = 100 * base["sem"] / base["n"]
        base["lat_med"] = llm_med
        # median per metric across runs
        for k in ("exact", "valid", "sem"):
            vals = sorted(r[k] for r in agg)
            base[k] = statistics.median(vals)
        results.append(base)
        print(f"LLM aggregated over {runs} run(s): exact={base['exact']}/{base['n']} "
              f"valid={base['valid']}/{base['n']} sem={base['sem']}/{base['n']} "
              f"lat_med={base['lat_med']:.0f}ms | rule_fallbacks={llm_fallback_count} (of {runs*base['n']})")

    # markdown table
    print("\n\n| Path | Exact-match | Valid | Equivalent | Median latency |")
    print("|---|---|---|---|---|")
    for r in results:
        print(f"| {r['label']} | {r['exact']}/{r['n']} ({r['exact_pct']:.1f}%) | "
              f"{r['valid']}/{r['n']} ({r['valid_pct']:.1f}%) | "
              f"{r['sem']}/{r['n']} ({r['sem_pct']:.1f}%) | {r['lat_med']:.0f} ms |")

    # per-class breakdown for rule-based (first result)
    r = results[0]
    print("\nClass breakdown (rule-based, exact-match):")
    for cls in ("RULE_OK", "RULE_NEAR", "LLM_ONLY"):
        n = sum(1 for g in GOLDEN if g["cls"] == cls)
        h = sum(1 for row, g in zip(r["rows"], GOLDEN) if g["cls"] == cls and row["exact"])
        print(f"  {cls:10s} {h}/{n}")

    print("\nPer-query detail (rule-based):")
    for row, g in zip(r["rows"], GOLDEN):
        mark = "=" if row["exact"] else ("~" if row["sem"] else "x")
        print(f"  [{mark}] ({g['cls']:8s}) {row['q'][:60]:62s} -> {row['sql'][:70]}")

    if len(results) > 1:
        llmr = results[1]
        print(f"\nPer-query detail (LLM):")
        for row, g in zip(llmr["rows"], GOLDEN):
            mark = "=" if row["exact"] else ("~" if row["sem"] else "x")
            print(f"  [{mark}] ({g['cls']:8s}) {row['q'][:48]:50s} {row['ms']:6.0f}ms -> {row['sql'][:70]}")
        print(f"\nLLM class breakdown (equivalent):")
        for cls in ("RULE_OK", "RULE_NEAR", "LLM_ONLY"):
            n = sum(1 for g in GOLDEN if g["cls"] == cls)
            h = sum(1 for row, g in zip(llmr["rows"], GOLDEN) if g["cls"] == cls and row["sem"])
            print(f"  {cls:10s} {h}/{n}")


def _llm_config():
    if os.environ.get("OPENROUTER_API_KEY"):
        return "https://openrouter.ai/api/v1/chat/completions", OPENROUTER_FALLBACK_MODELS
    if os.environ.get("OLLAMA_URL"):
        url = os.environ.get("OLLAMA_URL").rstrip("/") + "/api/generate"
        from text_to_sql import MODEL
        return url, [MODEL]
    return None


def _llm_guard(q, url, model, fallback=rule_gen):
    global llm_fallback_count
    try:
        raw = run_llm(q, url, model)
        sql = raw.strip()
        if sql.startswith("```sql"):
            sql = sql[6:]
        if sql.startswith("```"):
            sql = sql[3:]
        if sql.endswith("```"):
            sql = sql[:-3]
        sql = sql.strip().rstrip(";")
        if not sql.upper().startswith("SELECT"):
            llm_fallback_count += 1
            return fallback(q)
        return sql
    except Exception:
        llm_fallback_count += 1
        return fallback(q)


if __name__ == "__main__":
    main()