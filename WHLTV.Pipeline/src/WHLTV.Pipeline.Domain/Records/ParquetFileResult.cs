namespace WHLTV.Pipeline.Domain.Records;

public sealed record ParquetFileResult(
    string MapName,
    string ParquetPath,
    string PatchVersion
);
