using System.Text.Json;
using WHLTV.Pipeline.DataAccess.Repositories;
using WHLTV.Pipeline.Domain.Enums;
using WHLTV.Pipeline.Infrastructure.Storage;
using WHLTV.Pipeline.Infrastructure.Processes;

namespace WHLTV.DemoPipeline.Worker.Workers;

public sealed class ConvertWorker : BackgroundService
{
    private readonly DemoConversionJobRepository _jobs;
    private readonly PathResolver _pathResolver;
    private readonly ProcessRunner _processRunner;
    private readonly DemoPipelineLogsRepository _dbLogger;
    private readonly ILogger<ConvertWorker> _logger;
    private readonly AppConfigRepository _appConfigRepository;

    public ConvertWorker(
        DemoConversionJobRepository jobs,
        PathResolver pathResolver,
        ProcessRunner processRunner,
        DemoPipelineLogsRepository dbLogger,
        ILogger<ConvertWorker> logger,
        AppConfigRepository appConfigRepository
    )
    {
        _jobs = jobs;
        _pathResolver = pathResolver;
        _processRunner = processRunner;
        _dbLogger = dbLogger;
        _logger = logger;
        _appConfigRepository = appConfigRepository;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            var workerEnabled = await _appConfigRepository.GetWorkerEnabledStatus(PipelineWorkers.ConvertWorker);
            if (workerEnabled == false)
            {
                _logger.LogInformation("Extract worker is disabled.");
                await Task.Delay(TimeSpan.FromSeconds(30), stoppingToken);
                continue;
            }

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
                string extractedFolderFullPath = _pathResolver.GetWorkPath(job.ExtractedFolderRelativePath);

                if (!Directory.Exists(extractedFolderFullPath))
                {
                    throw new DirectoryNotFoundException(extractedFolderFullPath);
                }

                _logger.LogInformation("Converting demo folder {Folder} for conversion job {JobID}",
                                        extractedFolderFullPath,
                                        job.DemoConversionJobID);

                var result = await _processRunner.RunAsync("python",
                                                            $"-m DemoParser.cli \"{extractedFolderFullPath}\"",
                                                            stoppingToken);

                if (!result.Success)
                {
                    await _jobs.MarkFailed(
                        job.DemoConversionJobID,
                        result.StandardError
                    );
                    return;
                }

                var parquetFiles = JsonSerializer.Deserialize<ParquetFileResult[]>(
                    result.StandardOutput,
                    new JsonSerializerOptions { PropertyNameCaseInsensitive = true })
                    ?? throw new InvalidOperationException("Failed to deserialize RESULT_JSON.");

                // TODO:
                // create parquet file repo
                // create tblDemoParquetFiles records for each entry in parquetFiles

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

file sealed record ParquetFileResult(string MapName, string ParquetPath, string PatchVersion);