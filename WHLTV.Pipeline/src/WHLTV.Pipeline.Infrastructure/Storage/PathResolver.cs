using Microsoft.Extensions.Options;

namespace WHLTV.Pipeline.Infrastructure.Storage;

public sealed class PathResolver
{
    private readonly StorageOptions _options;

    public PathResolver(IOptions<StorageOptions> options)
    {
        _options = options.Value;
    }

    public string GetImportPath(string relativePath)
    {
        return Path.Combine(_options.ImportRoot, relativePath);
    }

    public string GetWorkPath(string relativePath)
    {
        return Path.Combine(_options.WorkRoot, relativePath);
    }

    public string ParquetRoot => _options.ParquetRoot;

    public string GetParquetPath(string relativePath)
    {
        return Path.Combine(_options.ParquetRoot, relativePath);
    }
}