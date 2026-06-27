import argparse
import json
import sys
from .services import convert_folder_to_parquet

def main():
	parser = argparse.ArgumentParser(description='Convert CS demo files in a folder to Parquet.')
	parser.add_argument('folder', type=str, help='Path to folder containing series demo files')
	parser.add_argument('-o', '--output-dir', type=str, default='ParquetFiles', help='Directory to write parquet output files to')
	args = parser.parse_args()

	folder = args.folder
	output_dir = args.output_dir

	print("Starting conversion...", file=sys.stderr)
	try:
		result = convert_folder_to_parquet(folder, output_dir=output_dir)
		print(f"Converted {len(result)} map group(s).", file=sys.stderr)
		print("Conversion complete.", file=sys.stderr)
		print(json.dumps(result))
	except BaseException as ex:
		if isinstance(ex, (KeyboardInterrupt, SystemExit)):
			raise
		print(f"Conversion failed: {ex}", file=sys.stderr)
		sys.exit(1)

if __name__ == "__main__":
	main()

