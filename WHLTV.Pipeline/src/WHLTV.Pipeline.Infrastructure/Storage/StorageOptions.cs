namespace WHLTV.Pipeline.Infrastructure.Storage;

public sealed class StorageOptions
{
    public required string ImportRoot { get; init; }
    public required string WorkRoot { get; init; }
    public required string ParquetRoot { get; init; }
}