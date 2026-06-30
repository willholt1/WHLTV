import argparse
import json
import sys
from .services import convert_folder_to_parquet
from .services.parquet_conversion_service import COMBINE_BATCH_SIZE, DEFAULT_CHUNK_SIZE

def main():
	parser = argparse.ArgumentParser(description='Convert CS demo files in a folder to Parquet.')
	parser.add_argument('folder', type=str, help='Path to folder containing series demo files')
	parser.add_argument('-o', '--output-dir', type=str, default='ParquetFiles', help='Directory to write parquet output files to')
	parser.add_argument(
		'-c', '--chunk-size',
		type=int,
		default=DEFAULT_CHUNK_SIZE,
		help=(
			'Approximate number of tick rows to buffer in memory per chunk before '
			'flushing to a temporary parquet file. Also caps the rows per temp file '
			'when writing large event tables. Lower values reduce peak memory usage '
			'but require more parse passes per demo (default: %(default)s).'
		),
	)
	parser.add_argument(
		'-b', '--combine-batch-size',
		type=int,
		default=COMBINE_BATCH_SIZE,
		help=(
			'Number of rows read/written at a time when combining the temporary '
			'parquet files into the final output (also the temp-file row-group size). '
			'Lower values reduce peak memory during the combine step at the cost of '
			'more output row groups (default: %(default)s).'
		),
	)
	args = parser.parse_args()

	folder = args.folder
	output_dir = args.output_dir
	chunk_size = args.chunk_size
	combine_batch_size = args.combine_batch_size

	print("Starting conversion...", file=sys.stderr)
	try:
		result = convert_folder_to_parquet(
			folder,
			output_dir=output_dir,
			chunk_size=chunk_size,
			combine_batch_size=combine_batch_size,
		)
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

