#!/usr/bin/env python
import argparse
import sys
import traceback

from pymongo import MongoClient
from pymongo.collation import Collation


def parse_args():
    p = argparse.ArgumentParser(
        description="Copy indexes from a source collection to a target collection in the same DB."
    )
    p.add_argument("--uri", required=False, default=None, help="MongoDB URI (overrides hardcoded)")
    p.add_argument("--db", required=True, help="Database name")
    p.add_argument("--source", required=True, help="Source collection name (take indexes from)")
    p.add_argument("--target", required=True, help="Target collection name (apply indexes to)")
    p.add_argument("--dry-run", action="store_true", help="Print indexes that would be created without applying them")
    p.add_argument("--background", action="store_true", help="Create indexes with background=True where supported")
    return p.parse_args()


def build_index_keys(key_doc):
    # key_doc can be a SON/dict/list — normalize to list of tuples
    try:
        if hasattr(key_doc, "items"):
            return list(key_doc.items())
        # assume iterable of pairs
        return [(k, v) for k, v in key_doc]
    except Exception:
        return list(key_doc)


def build_create_options(index_doc, use_background=False):
    opts = {}
    # Common options
    for k in ("unique", "sparse", "expireAfterSeconds", "hidden", "weights", "default_language", "language_override"):
        if k in index_doc:
            opts[k] = index_doc[k]

    # partialFilterExpression
    if "partialFilterExpression" in index_doc:
        opts["partialFilterExpression"] = index_doc["partialFilterExpression"]

    # name always preserved
    if "name" in index_doc:
        opts["name"] = index_doc["name"]

    # collation handling
    if "collation" in index_doc and index_doc["collation"]:
        try:
            col = index_doc["collation"]
            # Collation expects specific args; pass the dict as kwargs where possible
            opts["collation"] = Collation(**{k: v for k, v in col.items() if v is not None})
        except Exception:
            # If collation can't be constructed, skip it but log later
            opts["collation_error"] = True

    # background flag (optional)
    if use_background:
        opts["background"] = True

    return opts


def main():
    args = parse_args()

    # fallback URI from previous hardcoded value if not provided
    default_uri = "mongodb+srv://dabebe:ddemes@ubiquitystg.uniwl.mongodb.net"
    uri = args.uri or default_uri

    print("--- Index copy tool started ---")
    print(f"Connecting to: {uri} | DB: {args.db} | source: {args.source} -> target: {args.target}")

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=10000)
        db = client[args.db]
        src = db[args.source]
        tgt = db[args.target]

        print("Fetching index definitions from source collection...")
        indexes = list(src.list_indexes())
        print(f"Found {len(indexes)} indexes on {args.source}")

        created = 0
        skipped = 0
        errors = 0

        for idx in indexes:
            name = idx.get("name")
            # skip default _id index
            if name == "_id_":
                skipped += 1
                continue

            keys = build_index_keys(idx.get("key") or idx.get("keyDocument") or idx.get("keys"))
            opts = build_create_options(idx, use_background=args.background)

            # Remove unsupported placeholder flags
            collation_error = opts.pop("collation_error", False)

            if args.dry_run:
                print(
                    f"DRY-RUN: would create index '{opts.get('name')}' keys={keys} options={ {k:v for k,v in opts.items() if k!='name'} }"
                )
                if collation_error:
                    print("  NOTE: source index had collation but it could not be converted; review manually")
                continue

            try:
                print(f"Creating index '{opts.get('name')}' on {args.target} ...")
                # create_index accepts list of (key,direction)
                tgt.create_index(keys, **{k: v for k, v in opts.items() if k != "name"})
                created += 1
            except Exception as e:
                errors += 1
                print(f"ERROR creating index {name}: {e}")
                traceback.print_exc()

        print("--- Summary ---")
        print(f"Total indexes found: {len(indexes)}")
        print(f"Created: {created}, Skipped (including _id_): {skipped}, Errors: {errors}")

    except Exception as e:
        print(f"FATAL: {e}")
        traceback.print_exc()
        sys.exit(1)
    finally:
        try:
            client.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
