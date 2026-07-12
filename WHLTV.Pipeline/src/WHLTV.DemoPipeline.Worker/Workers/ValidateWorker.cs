using WHLTV.Pipeline.DataAccess.Repositories;
using WHLTV.Pipeline.Domain.Enums;

namespace WHLTV.DemoPipeline.Worker.Workers;

public sealed class ValidateWorker : BackgroundService
{
    private readonly DemoPipelineLogsRepository _dbLogger;
    private readonly ILogger<ValidateWorker> _logger;
    private readonly AppConfigRepository _appConfigRepository;

    public ValidateWorker(
        DemoPipelineLogsRepository dbLogger,
        ILogger<ValidateWorker> logger,
        AppConfigRepository appConfigRepository
    )
    {
        _dbLogger = dbLogger;
        _logger = logger;
        _appConfigRepository = appConfigRepository;
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
            
            /*
             * TODO:
             * - get validate job
             *      jobID/.parquet/.dem paths
             * - run python validation
             *      accept folder paths and match up map files
             *      need some way to unify .dem files
             *      will running validator in docker use too much memory??
             *      check awpy dfs parquet vs. dem
             *      output scoreboard
             * - get hltv data per map
             * - check hltv scoreboard vs awpy scoreboard
             *      some sort of %diff w/ a threshold for acceptance
             * - mark convert job as ReadyToStore
             * - maybe have a table or cols on tbldemoparquetfiles to store validation results
             */
            
        }
    }
}