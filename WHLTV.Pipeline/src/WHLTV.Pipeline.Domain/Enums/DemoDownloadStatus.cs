namespace WHLTV.Pipeline.Domain.Enums
{
    public enum DemoDownloadStatus
    {
        PendingDownload,
        Downloading,
        ReadyToExtract,
        Extracting,
        Extracted,
        Completed,
        Failed
    }
}
