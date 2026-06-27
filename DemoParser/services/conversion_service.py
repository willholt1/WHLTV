import os

from .parquet_conversion_service import demoToParquet


def find_demo_files(folder: str) -> list[str]:
    demo_files = []
    for file in os.listdir(folder):
        file_path = os.path.join(folder, file)
        if os.path.isfile(file_path) and file.endswith(".dem"):
            demo_files.append(file_path)
    return demo_files


def convert_folder_to_parquet(folder: str, output_dir: str = "ParquetFiles") -> list[dict]:
    if not os.path.isdir(folder):
        raise ValueError(f"{folder} is not a valid directory.")

    demo_files = find_demo_files(folder)
    if not demo_files:
        raise ValueError(f"No .dem files found in {folder}.")

    created_files = demoToParquet(demo_files, output_dir=output_dir)

    return [
        {
            "map_name": map_name,
            "parquet_path": parquet_path,
            "patch_version": patch_version,
        }
        for map_name, (parquet_path, patch_version) in created_files.items()
    ]
