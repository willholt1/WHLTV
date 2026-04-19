import argparse
import os
import sys
from . demoToParquet import demoToParquet

def find_demo_files(folder):
	demo_files = []
	for file in os.listdir(folder):
		file_path = os.path.join(folder, file)
		if os.path.isfile(file_path) and file.endswith('.dem'):
			demo_files.append(file_path)
	return demo_files

def main():
	parser = argparse.ArgumentParser(description='Convert CS demo files in a folder to Parquet.')
	parser.add_argument('folder', type=str, help='Path to folder containing series demo files')
	args = parser.parse_args()

	folder = args.folder
	if not os.path.isdir(folder):
		print(f"Error: {folder} is not a valid directory.")
		sys.exit(1)

	demo_files = find_demo_files(folder)
	if not demo_files:
		print(f"No .dem files found in {folder}.")
		sys.exit(1)

	print(f"Found {len(demo_files)} demo files. Starting conversion...")
	created_files, map_players = demoToParquet(demo_files)
	print("Conversion complete.")
	print("Created Parquet files:")
	for map_name, (parquet_path, patch_version) in created_files.items():
		print(f"{map_name}: {parquet_path} (patch {patch_version})")

if __name__ == "__main__":
	main()

