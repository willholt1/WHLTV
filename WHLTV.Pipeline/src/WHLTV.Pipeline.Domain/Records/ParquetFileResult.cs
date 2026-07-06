using System.Text.Json.Serialization;

namespace WHLTV.Pipeline.Domain.Records;

public sealed record ParquetFileResult(
    [property: JsonPropertyName("map_name")] string MapName,
    [property: JsonPropertyName("parquet_path")] string ParquetPath,
    [property: JsonPropertyName("patch_version")] string PatchVersion
);
