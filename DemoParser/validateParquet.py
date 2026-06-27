import argparse
from .services import run_all_validations


def main():
    parser = argparse.ArgumentParser(description="Verify Parquet vs Demo output.")
    parser.add_argument('--demo_file', type=str, help='Path to demo file')
    parser.add_argument('--parquet_file', type=str, help='Path to parquet file')
    parser.add_argument('--patch_version', type=str, help='Patch version to use for ParquetDemo')
    parser.add_argument('--map_name', type=str, help='Map name to use for ParquetDemo')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    debug = args.debug
    demo_file = args.demo_file
    map_name = args.map_name
    parquet_file = args.parquet_file
    patch_version = args.patch_version
    
    run_all_validations(
        demo_file=demo_file,
        parquet_file=parquet_file,
        patch_version=patch_version,
        map_name=map_name,
        debug=debug,
    )

if __name__ == "__main__":
	main()
