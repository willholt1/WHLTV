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
                _logger.LogInformation("No pending download jobs found.");
                await Task.Delay(TimeSpan.FromSeconds(10), stoppingToken);
                continue;
            }

            _logger.LogInformation(
                "Claimed download job {JobID} for match {MatchID}",
                job.DemoDownloadJobID,
                job.MatchID
            );

            var fakeArchivePath = $"demo-archives/job-{job.DemoDownloadJobID}/demo.rar";
            await _jobs.MarkReadyToExtract(job.DemoDownloadJobID, fakeArchivePath);

            _logger.LogInformation(
                "Marked job {JobID} as ReadyToExtract with archive path {ArchivePath}",
                job.DemoDownloadJobID,
                fakeArchivePath
            );

        }

    }
}