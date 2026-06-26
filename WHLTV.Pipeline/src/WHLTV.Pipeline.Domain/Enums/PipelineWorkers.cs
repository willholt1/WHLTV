namespace WHLTV.Pipeline.Domain.Enums
{
    public enum PipelineWorkers
    {
        DownloadWorker = 1,
        ExtractWorker = 2,
        ConvertWorker = 3,
        ValidateWorker = 4,
        StoreWorker = 5,
        CleanupWorker = 6
    }
}
