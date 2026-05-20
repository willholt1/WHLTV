namespace WHLTV.Pipeline.Domain.Jobs;

public sealed class DemoDownloadJob
{
    public int DemoDownloadJobID { get; set; }
    public int MatchID { get; set; }
    public string DemoLink { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public string? ArchiveRelativePath { get; set; }
    public int AttemptCount { get; set; }
}