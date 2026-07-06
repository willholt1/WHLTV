using System.Text.Json;
using WHLTV.Pipeline.DataAccess.Repositories;
using WHLTV.Pipeline.Domain.Enums;
using WHLTV.Pipeline.Domain.Records;
using WHLTV.Pipeline.Infrastructure.Storage;
using WHLTV.Pipeline.Infrastructure.Processes;

namespace WHLTV.DemoPipeline.Worker.Workers;

public sealed class ConvertWorker : BackgroundService
{
    private readonly DemoConversionJobRepository _jobs;
    private readonly DemoParquetFileRepository _parquetFiles;
    private readonly PathResolver _pathResolver;
    private readonly ProcessRunner _processRunner;
    private readonly DemoPipelineLogsRepository _dbLogger;
    private readonly ILogger<ConvertWorker> _logger;
    private readonly AppConfigRepository _appConfigRepository;

    public ConvertWorker(
        DemoConversionJobRepository jobs,
        DemoParquetFileRepository parquetFiles,
        PathResolver pathResolver,
        ProcessRunner processRunner,
        DemoPipelineLogsRepository dbLogger,
        ILogger<ConvertWorker> logger,
        AppConfigRepository appConfigRepository
    )
    {
        _jobs = jobs;
        _parquetFiles = parquetFiles;
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
                _logger.LogInformation("Convert worker is disabled.");
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

                string parquetOutputFolderFullPath = _pathResolver.GetParquetPath($"job-{job.DemoConversionJobID}");
                Directory.CreateDirectory(parquetOutputFolderFullPath);

                var result = await _processRunner.RunAsync("python3",
                                                            $"-m DemoParser.convertToParquet \"{extractedFolderFullPath}\" --output-dir \"{parquetOutputFolderFullPath}\"",
                                                            stoppingToken);

                if (!result.Success)
                {
                    var errorMessage = string.IsNullOrWhiteSpace(result.StandardError)
                        ? $"convertToParquet failed with exit code {result.ExitCode}"
                        : result.StandardError;

                    await _jobs.MarkFailed(
                        job.DemoConversionJobID,
                        errorMessage
                    );
                    await _dbLogger.LogStatusEnd(logID, exitCode: result.ExitCode, errorMessage: errorMessage);
                    continue;
                }

                var parquetFiles = JsonSerializer.Deserialize<ParquetFileResult[]>(
                    result.StandardOutput,
                    new JsonSerializerOptions { PropertyNameCaseInsensitive = true })
                    ?? throw new InvalidOperationException("Failed to deserialize RESULT_JSON.");


                foreach (var parquetFile in parquetFiles)
                {
                    _logger.LogInformation("mapName: {MapName}, patchVersion: {PatchVersion}, parquetPath: {ParquetPath}",
                                           parquetFile.MapName,
                                           parquetFile.PatchVersion,
                                           parquetFile.ParquetPath);
                }

                foreach (var parquetFile in parquetFiles)
                {
                    if (!Enum.TryParse<Map>(parquetFile.MapName, ignoreCase: true, out var mapEnum))
                    {
                        throw new InvalidOperationException(
                            $"Invalid map name '{parquetFile.MapName}' returned from convertToParquet."
                        );
                    }
                    var relativeParquetPath = Path.GetRelativePath(_pathResolver.ParquetRoot, parquetFile.ParquetPath);
                    await _parquetFiles.CreateDemoParquetFile(
                        job.DemoConversionJobID,
                        mapEnum,
                        parquetFile.PatchVersion,
                        relativeParquetPath
                    );
                }

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
