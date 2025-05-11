# glyphchain_cli.py
# Command-line interface for interacting with glyphchain_core

import argparse
import os
import json
from glyphchain_core import Glyph, GlyphEchoLog
from glyphchain_utils import timestamp_glyph, verify_glyph_timestamp


def create_new_glyph(args):
    core_concepts = [c.strip() for c in args.concepts.split(",")]
    glyph = Glyph(
        glyph_id=args.id,
        name=args.name,
        creator=args.creator,
        core_concepts=core_concepts
    )
    glyph.set_dedication(message=args.dedication, author=args.creator)
    glyph.set_closing(args.closing)
    
    os.makedirs(args.output_dir, exist_ok=True)
    output_path = os.path.join(args.output_dir, f"{args.id}_manifest.json")
    glyph.save(output_path)
    print(f"Glyph manifest saved to {output_path}")

def append_echo_entry(args):
    log = GlyphEchoLog()
    log.add_entry(
        node_id=args.node,
        vector=args.vector,
        assertion=args.assertion,
        trace_id=args.trace,
        symbol=args.symbol,
        meaning=args.meaning
    )
    log.save(args.output)
    print(f"Echo log saved to {args.output}")

def timestamp_glyph_manifest(args):
    try:
        # Load the glyph manifest
        with open(args.manifest, 'r') as f:
            glyph_data = json.load(f)
        
        # Create Glyph object from manifest
        glyph = Glyph(
            glyph_id=glyph_data['glyph_id'],
            name=glyph_data['name'],
            creator=glyph_data['creator'],
            core_concepts=glyph_data['core_concepts']
        )
        
        # Restore additional data
        if 'dedication' in glyph_data:
            glyph.dedication = glyph_data['dedication']
        if 'closing' in glyph_data:
            glyph.closing = glyph_data['closing']
        if 'registry' in glyph_data:
            glyph.registry = glyph_data['registry']
        
        # Save the glyph to ensure consistent format
        temp_path = f"{os.path.splitext(args.manifest)[0]}_temp.json"
        glyph.save(temp_path)
        
        try:
            # Create timestamp
            ots_path, timestamp_hash = timestamp_glyph(temp_path)
            print(f"OpenTimestamps proof saved to {ots_path}")
            print(f"Timestamp hash: {timestamp_hash}")
            
            # Verify the timestamp
            success, message = verify_glyph_timestamp(temp_path, ots_path)
            if success:
                print("✓ Timestamp verification successful")
                print(message)
            else:
                print("⚠ Timestamp verification failed")
                print(message)
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except FileNotFoundError as e:
        print(f"Error: {e}")
        exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in manifest file: {args.manifest}")
        exit(1)
    except Exception as e:
        print(f"Error creating timestamp: {e}")
        exit(1)

def main():
    parser = argparse.ArgumentParser(description="Glyphchain CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Create new glyph
    new_parser = subparsers.add_parser("new", help="Create a new glyph manifest")
    new_parser.add_argument("--id", required=True, help="Glyph ID")
    new_parser.add_argument("--name", required=True, help="Glyph name")
    new_parser.add_argument("--creator", required=True, help="Creator name")
    new_parser.add_argument("--concepts", required=True, help="Comma-separated core concepts")
    new_parser.add_argument("--dedication", default="", help="Dedication message")
    new_parser.add_argument("--closing", nargs="*", default=[], help="Closing lines")
    new_parser.add_argument("--output-dir", default="glyphs", help="Directory to save glyph")
    new_parser.set_defaults(func=create_new_glyph)

    # Add echo entry
    echo_parser = subparsers.add_parser("echo", help="Append a post-seal echo entry")
    echo_parser.add_argument("--node", required=True, help="Node ID")
    echo_parser.add_argument("--vector", required=True, help="Vector string")
    echo_parser.add_argument("--assertion", required=True, help="Assertion string")
    echo_parser.add_argument("--trace", help="Optional trace ID")
    echo_parser.add_argument("--symbol", help="Optional symbol")
    echo_parser.add_argument("--meaning", help="Optional symbolic meaning")
    echo_parser.add_argument("--output", default="glyph_echo_log.json", help="Output log file")
    echo_parser.set_defaults(func=append_echo_entry)

    # Add timestamp command
    timestamp_parser = subparsers.add_parser("timestamp", help="Create OpenTimestamps proof for a glyph manifest")
    timestamp_parser.add_argument("manifest", help="Path to the glyph manifest JSON file")
    timestamp_parser.set_defaults(func=timestamp_glyph_manifest)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
