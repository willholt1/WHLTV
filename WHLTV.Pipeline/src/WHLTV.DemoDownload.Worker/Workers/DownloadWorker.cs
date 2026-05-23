using WHLTV.Pipeline.DataAccess.Repositories;
using WHLTV.Pipeline.Infrastructure.Processes;
using WHLTV.Pipeline.Domain.Enums;

namespace WHLTV.DemoDownload.Worker.Workers;

public sealed class DownloadWorker : BackgroundService
{
    private readonly DemoDownloadJobRepository _jobs;
    private readonly DemoPipelineLogsRepository _logs;
    private readonly ProcessRunner _processRunner;
    private readonly ILogger<DownloadWorker> _logger;

    public DownloadWorker(
        DemoDownloadJobRepository jobs,
        DemoPipelineLogsRepository logs,
        ProcessRunner processRunner,
        ILogger<DownloadWorker> logger)
    {
        _jobs = jobs;
        _logs = logs;
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
            var logID = await _logs.LogStatusStart(PipelineEntityType.DemoDownloadJob
                                                 , job.DemoDownloadJobID
                                                 , DemoDownloadStatus.Downloading.ToString()
                                                 , PipelineStageStatus.Started);

            try
            {
                // Simulate download with a delay
                var fakeArchivePath = $"demo-archives/job-{job.DemoDownloadJobID}/demo.rar";
                await Task.Delay(TimeSpan.FromSeconds(30), stoppingToken);

                await _logs.LogStatusEnd(logID, exitCode: 0);
                await _jobs.MarkReadyToExtract(job.DemoDownloadJobID, fakeArchivePath);

                _logger.LogInformation(
                    "Marked job {JobID} as ReadyToExtract with archive path {ArchivePath}",
                    job.DemoDownloadJobID,
                    fakeArchivePath
                );
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error downloading demo for job {JobID}", job.DemoDownloadJobID);
                await _logs.LogStatusEnd(logID, exitCode: 1, errorMessage: ex.Message);
                continue;
            }

        }

    }
}