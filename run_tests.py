#!/usr/bin/env python3
"""Self-assessment runner for the TikTok Shop project.

It runs the public test suite and groups the results by the QUESTION of the
subject they check, so you can see at a glance what is done and what to do
next.

    python run_tests.py              # the whole suite, question by question
    python run_tests.py 13           # only question 13
    python run_tests.py 13 19 20     # several questions
    python run_tests.py --failed     # only what is failing or missing
    python run_tests.py --traceback  # the FULL error of each problem

Each test is reported as one of:
    \u2705  the test passed;
    \u274c  your code ran but produced a wrong result (the reason is shown);
    \u23f3  the function or route is not implemented yet.
"""

import contextlib
import io
import os
import sys
from collections import Counter, OrderedDict

try:
    import pytest
except ModuleNotFoundError:
    sys.exit(
        "pytest is not installed for this interpreter.\n"
        f"Install the test dependencies with:\n"
        f"  {sys.executable} -m pip install -r requirements.txt"
    )

# ---------------------------------------------------------------------------
# Colours (dropped when the output is redirected, or when NO_COLOR is set)
# ---------------------------------------------------------------------------
COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ
GREEN, RED, YELLOW, GREY, BOLD, RESET = (
    ("\033[32m", "\033[31m", "\033[33m", "\033[90m", "\033[1m", "\033[0m")
    if COLOR else ("",) * 6
)
STATUS_COLOR = {"SUCCESS": GREEN, "FAILED": RED, "ERROR": RED,
                "TODO": YELLOW, "SKIPPED": GREY}
# One glyph per outcome, so a report can be read at a glance.
STATUS_MARK = {"SUCCESS": "\u2705", "FAILED": "\u274c", "ERROR": "\U0001f4a5",
               "TODO": "\u23f3", "SKIPPED": "\u26aa"}


# ---------------------------------------------------------------------------
# Which question of the subject does each test check?
# ---------------------------------------------------------------------------
QUESTIONS = OrderedDict([
    (3, {
        "title": "Generate one CSV file per entity",
        "where": "data/process_data.py",
        "tests": [
            "test_process_creators",
            "test_process_videos",
            "test_process_spends",
            "test_process_products",
            "test_process_customers",
            "test_process_users",
            "test_process_orders",
            "test_process_contains",
        ],
    }),
    (4, {
        "title": "Load the configuration of the application",
        "where": "utils.py (load_config)",
        "tests": [
            "test_load_config_returns_a_dictionary",
            "test_load_config_reads_the_database_path",
            "test_load_config_reads_the_secret_key",
            "test_load_config_reads_every_line",
            "test_load_config_splits_the_key_from_the_value",
        ],
    }),
    (5, {
        "title": "Create the tables of the database",
        "where": "db/__init__.py (create_database)",
        "tests": [
            "test_every_table_is_created",
            "test_every_table_has_its_columns",
            "test_primary_keys_are_declared",
            "test_the_foreign_keys_are_declared",
            "test_the_money_rules_are_enforced",
        ],
    }),
    (6, {
        "title": "Load the CSV files into the database",
        "where": "db/__init__.py (populate_database)",
        "tests": [
            "test_populate_returns_true",
            "test_every_table_is_filled",
            "test_the_values_are_loaded_as_they_are",
            "test_the_reserved_name_order_is_quoted",
            "test_the_foreign_keys_still_match",
        ],
    }),
    (7, {
        "title": "Create AND fill the database in one call",
        "where": "db/__init__.py (init_database)",
        "tests": [
            "test_init_database_creates_the_schema",
            "test_init_database_loads_every_file",
            "test_init_database_loads_in_a_valid_order",
        ],
    }),
    (11, {
        "title": "Update the password of a user",
        "where": "db/users.py (update_password)",
        "tests": [
            "test_update_password_changes_only_that_user",
        ],
    }),
    (13, {
        "title": "Read and write the database",
        "where": "db/creators.py, db/videos.py, db/products.py, "
                 "db/customers.py, db/orders.py, db/users.py",
        "tests": [
            "test_get_creator",
            "test_get_creator_unknown_returns_an_empty_dict",
            "test_get_creators",
            "test_insert_creator",
            "test_insert_creator_refuses_a_duplicate",
            "test_update_creator_followers",
            "test_get_creator_videos",
            "test_get_creators_without_sales",
            "test_get_video",
            "test_get_video_unknown_returns_an_empty_dict",
            "test_get_videos",
            "test_insert_video",
            "test_get_video_orders_count",
            "test_get_video_orders_count_without_any_order",
            "test_get_best_videos_puts_the_money_losing_video_last",
            "test_get_best_videos_returns_only_n_videos",
            "test_get_product",
            "test_get_product_unknown_returns_an_empty_dict",
            "test_get_products",
            "test_get_products_by_category",
            "test_insert_product",
            "test_update_product_stock",
            "test_decrease_product_stock",
            "test_decrease_product_stock_refuses_to_go_negative",
            "test_get_low_stock_products",
            "test_get_quantity_sold",
            "test_get_quantity_sold_of_a_product_nobody_ordered",
            "test_get_customer",
            "test_get_customer_unknown_returns_an_empty_dict",
            "test_get_customers",
            "test_insert_customer",
            "test_update_customer_country",
            "test_get_products_bought_by_customer",
            "test_get_total_spent_by_customer_ignores_refunds",
            "test_get_total_spent_by_a_customer_who_never_ordered",
            "test_get_order",
            "test_get_order_unknown_returns_an_empty_dict",
            "test_get_orders",
            "test_get_orders_by_customer",
            "test_insert_order",
            "test_insert_order_line",
            "test_get_order_lines",
            "test_get_order_total",
            "test_get_order_total_of_an_unknown_order",
            "test_get_user",
            "test_get_users",
            "test_get_orders_handled_by_user",
        ],
    }),
    (17, {
        "title": "The routes about the users",
        "where": "routes/users.py, app.py",
        "tests": [
            "test_the_users_blueprint_is_registered",
            "test_get_all_users",
            "test_get_one_user",
            "test_get_an_unknown_user_is_404",
            "test_add_user",
            "test_add_user_without_a_password",
            "test_register_open",
            "test_get_user_with_token",
        ],
    }),
    (18, {
        "title": "The debug routes",
        "where": "routes/data.py",
        "tests": ["test_data_creators", "test_data_products",
                  "test_data_orders"],
    }),
    (19, {
        "title": "The routes about creators, videos, products and orders",
        "where": "routes/creators.py, routes/products.py, routes/orders.py",
        "tests": [
            "test_get_creator_route",
            "test_get_an_unknown_creator_is_404",
            "test_get_creator_videos_route",
            "test_get_video_route",
            "test_get_product_route",
            "test_get_an_unknown_product_is_404",
            "test_get_low_stock_products_route",
            "test_get_quantity_sold_route",
            "test_get_order_carries_its_lines_and_its_total",
            "test_get_an_unknown_order_is_404",
            "test_get_customer_route",
        ],
    }),
    (20, {
        "title": "Hash the passwords",
        "where": "utils.py (hash_password, check_password, check_user)",
        "tests": [
            "test_hash_password_does_not_keep_the_plain_text",
            "test_check_password_tells_the_right_one_from_the_wrong_one",
            "test_check_user_against_the_database",
            "test_check_user_refuses_a_wrong_password",
        ],
    }),
    (21, {
        "title": "Store the hash, not the password",
        "where": "db/users.py (insert_user)",
        "tests": ["test_insert_user_stores_a_hash"],
    }),
    (22, {
        "title": "Generate and check a token",
        "where": "utils.py (generate_token, check_token)",
        "tests": [
            "test_generate_token_returns_a_token",
            "test_check_token_reads_the_username_back",
            "test_check_token_refuses_a_tampered_token",
            "test_the_token_expires",
        ],
    }),
    (23, {
        "title": "Get a token with POST /login",
        "where": "routes/auth.py",
        "tests": [
            "test_login_success",
            "test_login_returns_a_usable_token",
            "test_login_wrong_password",
            "test_login_missing_password",
        ],
    }),
    (24, {
        "title": "Protect the routes with a token",
        "where": "routes/*.py (@token_required)",
        "tests": ["test_users_list_requires_token",
                  "test_patch_password_with_token",
                  "test_patch_password_without_a_password"],
    }),
])

# test name -> question number
QUESTION_OF = {name: number
               for number, question in QUESTIONS.items()
               for name in question["tests"]}


class NodeCollector:
    """Collect the node id of every test, without running anything."""

    def __init__(self):
        self.nodeids = []

    def pytest_collection_modifyitems(self, items):
        self.nodeids.extend(item.nodeid for item in items)


def collect_nodeids():
    """{test name: node id} for the whole public suite."""
    collector = NodeCollector()
    with contextlib.redirect_stdout(io.StringIO()):
        pytest.main(["-q", "--collect-only", "-p", "no:cacheprovider",
                     "tests/public"], plugins=[collector])
    return {nodeid.rsplit("::", 1)[-1].split("[")[0]: nodeid
            for nodeid in collector.nodeids}


class StatusCollector:
    """Collect a status (and a reason when it failed) per test."""

    def __init__(self):
        self.status = {}
        self.reason = {}
        self.detail = {}     # the whole traceback, shown with --traceback
        self.nodeid = {}     # to re-run one test with pytest


    def _set(self, name, value, reason="", detail="", nodeid=""):
        if self.status.get(name) in ("FAILED", "ERROR"):
            return
        self.status[name] = value
        if reason:
            self.reason[name] = reason
        if detail:
            self.detail[name] = detail
        if nodeid:
            self.nodeid[name] = nodeid

    def pytest_runtest_logreport(self, report):
        name = report.nodeid.rsplit("::", 1)[-1].split("[")[0]
        if report.skipped:
            text = (report.longrepr[2] if isinstance(report.longrepr, tuple)
                    else str(report.longrepr))
            self._set(name, "TODO" if "TODO" in text else "SKIPPED",
                      text.replace("Skipped: ", "").strip(),
                      nodeid=report.nodeid)
        elif report.when == "call":
            if report.passed:
                self._set(name, "SUCCESS", nodeid=report.nodeid)
            else:
                self._set(name, "FAILED", self._short(report),
                          str(report.longrepr), report.nodeid)
        elif report.failed:
            self._set(name, "ERROR", self._short(report),
                      str(report.longrepr), report.nodeid)

    @staticmethod
    def _short(report):
        """The line of the traceback that says what went wrong.

        pytest marks it with a leading "E"; the following "+ where ..." lines
        only detail the values, so the first "E" line is the useful one.
        """
        text = str(getattr(report, "longrepr", "")).strip()
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for line in lines:
            if line.startswith("E ") or line == "E":
                return line[1:].strip()[:160] or ""
        for line in reversed(lines):
            if not line.startswith(("_", "=", "-")):
                return line[:160]
        return ""


def bar(done, total, width=20):
    filled = round(width * done / total) if total else 0
    return f"[{'#' * filled}{'-' * (width - filled)}]"


def main():
    arguments = sys.argv[1:]
    only_problems = "--failed" in arguments
    full_traceback = "--traceback" in arguments or "-t" in arguments
    wanted = {int(a) for a in arguments if a.isdigit()}
    unknown = wanted - set(QUESTIONS)
    if unknown:
        sys.exit(f"No test is attached to question(s) {sorted(unknown)}.\n"
                 f"Questions covered by the tests: {sorted(QUESTIONS)}")

    # The tests are always handed to pytest question by question, in the order
    # of the subject: what you watch scroll past is then in the same order as
    # the report printed at the end. Asking for questions simply keeps fewer.
    nodeids = collect_nodeids()
    numbers = sorted(wanted) if wanted else list(QUESTIONS)
    targets = [nodeids[name]
               for number in numbers
               for name in QUESTIONS[number]["tests"]
               if name in nodeids]
    if not wanted:
        # A test that no question claims would never run: keep it at the end
        # rather than lose it silently.
        targets += [nodeid for name, nodeid in nodeids.items()
                    if name not in QUESTION_OF]
    if not targets:
        sys.exit("None of the tests of that question could be collected.\n"
                 "Run the whole suite to see the error: "
                 "python run_tests.py")

    if wanted:
        print(f"{GREY}Running the {len(targets)} test(s) of question(s) "
              f"{', '.join(str(n) for n in sorted(wanted))} ...{RESET}",
              flush=True)
    else:
        print(f"{GREY}Running the tests ...{RESET}", flush=True)

    collector = StatusCollector()
    # pytest prints its own report; we only want ours, so it is swallowed.
    with contextlib.redirect_stdout(io.StringIO()):
        pytest.main(["-q", "--no-header",
                     "--tb=long" if full_traceback else "--tb=line",
                     "-p", "no:cacheprovider", *targets],
                    plugins=[collector])

    print(f"\n{BOLD}==================== Test report ===================={RESET}")

    overall = Counter()
    for number, question in QUESTIONS.items():
        results = [(name, collector.status.get(name, "SKIPPED"))
                   for name in question["tests"]]
        overall.update(status for _, status in results)
        if wanted and number not in wanted:
            continue

        done = sum(1 for _, status in results if status == "SUCCESS")
        total = len(results)
        color = GREEN if done == total else YELLOW if done else RED
        print(f"\n{BOLD}Question {number}{RESET} - {question['title']}")
        print(f"  {GREY}{question['where']}{RESET}")
        print(f"  {color}{bar(done, total)} {done}/{total}{RESET}")

        for name, status in results:
            if only_problems and status == "SUCCESS":
                continue
            color = STATUS_COLOR.get(status, "")
            glyph = STATUS_MARK.get(status, "")
            print(f"    {glyph} {color}{name}{RESET}")
            if status in ("FAILED", "ERROR"):
                if full_traceback and collector.detail.get(name):
                    for line in collector.detail[name].splitlines():
                        print(f"              {GREY}{line}{RESET}")
                    print(f"              {GREY}re-run it with: python -m "
                          f"pytest {collector.nodeid.get(name, '')} -vv{RESET}")
                elif collector.reason.get(name):
                    print(f"              {GREY}{collector.reason[name]}{RESET}")
            # Why a test is TODO is only worth printing when you asked about
            # it: at the start of the project everything is TODO.
            elif status == "TODO" and (only_problems or wanted):
                if collector.reason.get(name):
                    print(f"              {GREY}{collector.reason[name]}{RESET}")

    if wanted:
        overall = Counter(
            collector.status.get(name, "SKIPPED")
            for number in wanted for name in QUESTIONS[number]["tests"])

    total = sum(overall.values())
    success = overall.get("SUCCESS", 0)
    failed = overall.get("FAILED", 0) + overall.get("ERROR", 0)
    todo = overall.get("TODO", 0) + overall.get("SKIPPED", 0)

    print(f"\n{BOLD}====================================================={RESET}")
    print(f"  {GREEN}{STATUS_MARK['SUCCESS']} {success}{RESET}   "
          f"{RED}{STATUS_MARK['FAILED']} {failed}{RESET}   "
          f"{YELLOW}{STATUS_MARK['TODO']} {todo}{RESET}   (total {total})")
    percent = (100 * success // total) if total else 0
    color = GREEN if percent >= 80 else YELLOW if percent >= 50 else RED
    print(f"  Score: {color}{bar(success, total, 30)} {success}/{total} "
          f"({percent}%){RESET}")

    skipped = overall.get("SKIPPED", 0)
    if skipped:
        print(f"  {GREY}{STATUS_MARK['SKIPPED']} {skipped} test(s) could not be "
              f"found in ./tests: this runner knows their name but the file "
              f"does not\n     define them. Your tests/ directory is probably "
              f"out of date -- ask for the\n     current one.{RESET}")

    if failed and not full_traceback:
        print(f"  {GREY}Run 'python run_tests.py --traceback' to see "
              f"the full error of each failing test.{RESET}")

    remaining = [str(number) for number, question in QUESTIONS.items()
                 if (not wanted or number in wanted)
                 and any(collector.status.get(name, "SKIPPED") != "SUCCESS"
                         for name in question["tests"])]
    if remaining:
        print(f"  {GREY}Questions left to finish: {', '.join(remaining)}{RESET}")
    else:
        print(f"  {GREEN}Every question checked by the tests is done.{RESET}")
    print(f"{BOLD}====================================================={RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
