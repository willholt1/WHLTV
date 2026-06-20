using WHLTV.Pipeline.DataAccess.Repositories;
using WHLTV.Pipeline.Domain.Enums;
using WHLTV.Pipeline.Infrastructure.Archives;
using WHLTV.Pipeline.Infrastructure.Storage;

namespace WHLTV.DemoPipeline.Worker.Workers;

public sealed class ConvertWorker : BackgroundService
{
    private readonly DemoFileJobRepository _jobs;
    private readonly PathResolver _pathResolver;
    private readonly DemoPipelineLogsRepository _dbLogger;
    private readonly ILogger<ConvertWorker> _logger;

    public ConvertWorker(
        DemoFileJobRepository jobs,
        PathResolver pathResolver,
        DemoPipelineLogsRepository dbLogger,
        ILogger<ConvertWorker> logger
    )
    {
        _jobs = jobs;
        _pathResolver = pathResolver;
        _dbLogger = dbLogger;
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            var job = await _jobs.TryClaimPendingConvertJob();

            if (job is null)
            {
                _logger.LogInformation("No pending convert jobs found.");
                await Task.Delay(TimeSpan.FromSeconds(30), stoppingToken);
                continue;
            }

            _logger.LogInformation(
                "Claimed convert job {JobID}",
                job.DemoFileJobID
            );
            var logID = await _dbLogger.LogStatusStart(PipelineEntityType.DemoFileJob
                                                 , job.DemoFileJobID
                                                 , DemoFileStatus.Converting.ToString()
                                                 , PipelineStageStatus.Started);

            try
            {
                // Mock conversion
                await Task.Delay(TimeSpan.FromSeconds(5), stoppingToken);

                await _jobs.MarkReadyToValidate(job.DemoFileJobID);
                _logger.LogInformation(
                    "Marked job {JobID} as Ready to Validate",
                    job.DemoFileJobID
                );

            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error converting demo for job {JobID}", job.DemoFileJobID);
                await _dbLogger.LogStatusEnd(logID, exitCode: 1, errorMessage: ex.Message);
                await _jobs.MarkFailed(job.DemoFileJobID, ex.Message);
                continue;
            }

        }

    }
}