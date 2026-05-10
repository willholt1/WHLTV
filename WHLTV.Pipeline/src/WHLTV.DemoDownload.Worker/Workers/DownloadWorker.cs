using WHLTV.Pipeline.DataAccess.Repositories;
using WHLTV.Pipeline.Infrastructure.Processes;

namespace WHLTV.DemoDownload.Worker.Workers;

public sealed class DownloadWorker : BackgroundService
{
    private readonly DemoDownloadJobRepository _jobs;
    private readonly ProcessRunner _processRunner;
    private readonly ILogger<DownloadWorker> _logger;

    public DownloadWorker(
        DemoDownloadJobRepository jobs,
        ProcessRunner processRunner,
        ILogger<DownloadWorker> logger)
    {
        _jobs = jobs;
        _processRunner = processRunner;
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            var job = await _jobs.TryClaimPendingDownloadJob();

            if (job is null)
            {
                await Task.Delay(TimeSpan.FromSeconds(30), stoppingToken);
                continue;
            }

            try
            {
                _logger.LogInformation("Downloading demo job {JobID}", job.DemoDownloadJobID);

                // Later: build docker run command properly from config.
                var result = await _processRunner.RunAsync(
                    "docker",
                    $"run --rm your-downloader-image --url \"{job.DemoUrl}\"",
                    stoppingToken
                );

                if (!result.Success)
                {
                    await _jobs.MarkFailed(job.DemoDownloadJobID, result.StandardError);
                    continue;
                }

                await _jobs.MarkReadyToExtract(
                    job.DemoDownloadJobID,
                    archiveRelativePath: $"demo-archives/job-{job.DemoDownloadJobID}/demo.rar"
                );
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Download job {JobID} failed", job.DemoDownloadJobID);
                await _jobs.MarkFailed(job.DemoDownloadJobID, ex.Message);
            }
        }
    }
}