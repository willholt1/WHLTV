using WHLTV.Pipeline.DataAccess.Repositories;
using WHLTV.Pipeline.Domain.Enums;
using WHLTV.Pipeline.Infrastructure.Archives;
using WHLTV.Pipeline.Infrastructure.Storage;

namespace WHLTV.DemoPipeline.Worker.Workers;

public sealed class ConvertWorker : BackgroundService
{
    private readonly DemoConversionJobRepository _jobs;
    private readonly PathResolver _pathResolver;
    private readonly DemoPipelineLogsRepository _dbLogger;
    private readonly ILogger<ConvertWorker> _logger;

    public ConvertWorker(
        DemoConversionJobRepository jobs,
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
                job.DemoConversionJobID
            );
            var logID = await _dbLogger.LogStatusStart(PipelineEntityType.DemoConversionJob
                                                 , job.DemoConversionJobID
                                                 , DemoConversionStatus.Converting.ToString()
                                                 , PipelineStageStatus.Started);

            try
            {
                // Mock conversion
                await Task.Delay(TimeSpan.FromSeconds(5), stoppingToken);

                await _jobs.MarkReadyToValidate(job.DemoConversionJobID);
                _logger.LogInformation(
                    "Marked job {JobID} as Ready to Validate",
                    job.DemoConversionJobID
                );

                await _dbLogger.LogStatusEnd(logID, exitCode: 0);

            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error converting demo for job {JobID}", job.DemoConversionJobID);
                await _dbLogger.LogStatusEnd(logID, exitCode: 1, errorMessage: ex.Message);
                await _jobs.MarkFailed(job.DemoConversionJobID, ex.Message);
                continue;
            }

        }

    }
}