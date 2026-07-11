using WHLTV.Pipeline.DataAccess.Repositories;
using WHLTV.Pipeline.Infrastructure.Docker;
using WHLTV.Pipeline.Domain.Enums;

namespace WHLTV.DemoDownload.Worker.Workers;

public sealed class DownloadWorker : BackgroundService
{
    private readonly DemoDownloadJobRepository _jobs;
    private readonly DemoPipelineLogsRepository _dbLogger;
    private readonly DockerRunner _dockerRunner;
    private readonly ILogger<DownloadWorker> _logger;
    private readonly string _outputDirectoryRoot;
    private readonly string _imageName;

    public DownloadWorker(
        DemoDownloadJobRepository jobs,
        DemoPipelineLogsRepository dbLogger,
        DockerRunner dockerRunner,
        IConfiguration configuration,
        ILogger<DownloadWorker> logger)
    {
        _jobs = jobs;
        _dbLogger = dbLogger;
        _dockerRunner = dockerRunner;
        _outputDirectoryRoot = configuration["DownloadWorker:OutputDirectory"]
            ?? throw new InvalidOperationException("Missing required configuration: DownloadWorker:OutputDirectory");
        _imageName = configuration["DownloadWorker:ImageName"]
            ?? throw new InvalidOperationException("Missing required configuration: DownloadWorker:ImageName");

        if (string.IsNullOrWhiteSpace(_outputDirectoryRoot))
        {
            throw new InvalidOperationException("Configuration DownloadWorker:OutputDirectory must not be empty.");
        }

        if (string.IsNullOrWhiteSpace(_imageName))
        {
            throw new InvalidOperationException("Configuration DownloadWorker:ImageName must not be empty.");
        }
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
                await Task.Delay(TimeSpan.FromSeconds(30), stoppingToken);
                continue;
            }

            _logger.LogInformation(
                "Claimed download job {JobID} for match {MatchID}",
                job.DemoDownloadJobID,
                job.MatchID
            );
            var logId = await _dbLogger.LogStatusStart(PipelineEntityType.DemoDownloadJob
                                                 , job.DemoDownloadJobID
                                                 , DemoDownloadStatus.Downloading.ToString()
                                                 , PipelineStageStatus.Started);

            try
            {
                var outputDirectory = Path.GetFullPath(Path.Combine(_outputDirectoryRoot, $"job-{job.DemoDownloadJobID}"));
                Directory.CreateDirectory(outputDirectory);
                var result = await _dockerRunner.RunAsync(
                    new DockerRunOptions
                    {
                        ImageName = _imageName,
                        VolumeMounts =
                        {
                            [outputDirectory] = "/app/DemoFiles"
                        },
                        Arguments =
                        {
                            job.DemoLink
                        },
                        RemoveWhenFinished = true
                    },
                    stoppingToken
                );

                _logger.LogInformation("Docker stdout: {Stdout}", result.StandardOutput);
                _logger.LogInformation("Docker stderr: {Stderr}", result.StandardError);

                await _dbLogger.LogStatusEnd(logId, exitCode: result.ExitCode);

                if (result.ExitCode == 0)
                {
                    await _jobs.MarkReadyToExtract(job.DemoDownloadJobID, outputDirectory);
                    _logger.LogInformation(
                        "Marked job {JobID} as ReadyToExtract with path {outputDirectory}",
                        job.DemoDownloadJobID,
                        outputDirectory
                    );
                }
                else
                {
                    var errorMsg = $"Docker process failed with exit code {result.ExitCode}. See logs for details.";
                    await _jobs.MarkFailed(job.DemoDownloadJobID, errorMsg);
                    _logger.LogWarning(errorMsg);
                }

                await Task.Delay(TimeSpan.FromSeconds(30), stoppingToken);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error downloading demo for job {JobID}", job.DemoDownloadJobID);
                await _dbLogger.LogStatusEnd(logId, exitCode: 1, errorMessage: ex.Message);
                await _jobs.MarkFailed(job.DemoDownloadJobID, ex.Message);
            }

        }

    }
}