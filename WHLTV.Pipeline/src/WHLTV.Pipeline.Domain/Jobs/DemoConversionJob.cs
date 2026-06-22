namespace WHLTV.Pipeline.Domain.Jobs;

public sealed class DemoConversionJob
{
    public int DemoConversionJobID { get; set; }
    public int DemoDownloadJobID { get; set; }
    public string ExtractedFolderRelativePath { get; set; } = string.Empty;
    public string ParquetTempFolderRelativePath { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public int AttemptCount { get; set; }
}