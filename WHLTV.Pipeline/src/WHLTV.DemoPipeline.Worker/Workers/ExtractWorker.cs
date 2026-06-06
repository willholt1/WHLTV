using WHLTV.Pipeline.DataAccess.Repositories;
using WHLTV.Pipeline.Infrastructure.Processes;
using WHLTV.Pipeline.Domain.Enums;
using System.Reflection.Metadata.Ecma335;

namespace WHLTV.DemoPipeline.Worker.Workers;

public sealed class ExtractWorker : BackgroundService
{
    private readonly DemoDownloadJobRepository _jobs;
    private readonly DemoPipelineLogsRepository _dbLogger;
    private readonly ILogger<ExtractWorker> _logger;

    public ExtractWorker(
        DemoDownloadJobRepository jobs,
        DemoPipelineLogsRepository dbLogger,
        ILogger<ExtractWorker> logger)
    {
        _jobs = jobs;
        _dbLogger = dbLogger;
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            var job = await _jobs.TryClaimPendingExtractJob();

            if (job is null)
            {
                _logger.LogInformation("No pending extract jobs found.");
                await Task.Delay(TimeSpan.FromSeconds(10), stoppingToken);
                continue;
            }

            _logger.LogInformation(
                "Claimed extract job {JobID} for match {MatchID}",
                job.DemoDownloadJobID,
                job.MatchID
            );
            var logID = await _dbLogger.LogStatusStart(PipelineEntityType.DemoDownloadJob
                                                 , job.DemoDownloadJobID
                                                 , DemoDownloadStatus.Extracting.ToString()
                                                 , PipelineStageStatus.Started);

            try
            {
                Console.WriteLine($"Extracting demo for job {job.DemoDownloadJobID} from archive path {job.ArchiveRelativePath}");
                await Task.Delay(TimeSpan.FromSeconds(5), stoppingToken); // Simulate work
                var exitCode = 0; // Simulate success

                if (exitCode == 0)
                {
                    await _jobs.MarkExtracted(job.DemoDownloadJobID);
                    _logger.LogInformation(
                        "Marked job {JobID} as Extracted",
                        job.DemoDownloadJobID
                    );
                }
                else
                {
                    var errorMsg = $"Extract process failed with exit code {exitCode}. See logs for details.";
                    await _jobs.MarkFailed(job.DemoDownloadJobID, errorMsg);
                    _logger.LogWarning(errorMsg);
                }

                await Task.Delay(TimeSpan.FromSeconds(10), stoppingToken);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error downloading demo for job {JobID}", job.DemoDownloadJobID);
                await _dbLogger.LogStatusEnd(logID, exitCode: 1, errorMessage: ex.Message);
                await _jobs.MarkFailed(job.DemoDownloadJobID, ex.Message);
                continue;
            }

        }

    }
}