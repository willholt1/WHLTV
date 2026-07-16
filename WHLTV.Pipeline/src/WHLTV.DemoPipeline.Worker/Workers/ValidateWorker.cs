using System.Security.Cryptography;
using WHLTV.Pipeline.DataAccess.Repositories;
using WHLTV.Pipeline.Domain.Enums;

namespace WHLTV.DemoPipeline.Worker.Workers;

public sealed class ValidateWorker : BackgroundService
{
    private readonly DemoPipelineLogsRepository _dbLogger;
    private readonly ILogger<ValidateWorker> _logger;
    private readonly AppConfigRepository _appConfigRepository;
    private readonly DemoConversionJobRepository _jobs;

    public ValidateWorker(
        DemoPipelineLogsRepository dbLogger,
        ILogger<ValidateWorker> logger,
        AppConfigRepository appConfigRepository,
        DemoConversionJobRepository jobs
    )
    {
        _dbLogger = dbLogger;
        _logger = logger;
        _appConfigRepository = appConfigRepository;
        _jobs = jobs;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            var workerEnabled = await _appConfigRepository.GetWorkerEnabledStatus(PipelineWorkers.ValidateWorker);
            if (workerEnabled == false)
            {
                _logger.LogInformation("Validate worker is disabled.");
                await Task.Delay(TimeSpan.FromSeconds(30), stoppingToken);
                continue;
            }

            var job = await _jobs.TryClaimPendingValidateJob();

            if (job is null)
            {
                _logger.LogInformation("No pending validate jobs found.");
                await Task.Delay(TimeSpan.FromSeconds(30), stoppingToken);
                continue;
            }

            _logger.LogInformation(
                "Claimed validate job {JobID}",
                job.DemoConversionJobID
            );

            var logId = await _dbLogger.LogStatusStart(PipelineEntityType.DemoConversionJob
                , job.DemoConversionJobID
                , DemoConversionStatus.Validating.ToString()
                , PipelineStageStatus.Started);

            try
            {
                // Run python validation script
                // log df comparison results
                // get hltv stats from db
                // check scoreboard against hltv data k/d/a/adr etc.
                // express diff as pct, threshold from db config
                // log validation results to db
                // mark as ReadyToStore if ok, 

            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error validating demo for job {JobID}", job.DemoConversionJobID);
                await _dbLogger.LogStatusEnd(logId, exitCode: 1, errorMessage: ex.Message);
                await _jobs.MarkFailed(job.DemoConversionJobID, ex.Message);
            }


            /*
             * TODO:
             * - run python validation
             *      accept folder paths and match up map files
             *      need some way to unify .dem files
             *      will running validator in docker use too much memory??
             *      check awpy dfs parquet vs. dem
             *      output scoreboard
             */

        }
    }
}