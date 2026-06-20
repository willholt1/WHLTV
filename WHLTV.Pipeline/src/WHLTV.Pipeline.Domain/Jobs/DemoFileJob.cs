namespace WHLTV.Pipeline.Domain.Jobs;

public sealed class DemoFileJob
{
    public int DemoFileJobID { get; set; }
    public int DemoDownloadJobID { get; set; }
    public string DemoRelativePath { get; set; } = string.Empty;
    public string ParquetTempRelativePath { get; set; } = string.Empty;
    public string ParquetFinalRelativePath { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public int AttemptCount { get; set; }
}