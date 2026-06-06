using WHLTV.Pipeline.DataAccess.Repositories;
using WHLTV.Pipeline.Infrastructure.Processes;
using WHLTV.Pipeline.Infrastructure.Docker;
using WHLTV.Pipeline.Domain.Enums;
using System.Reflection.Metadata.Ecma335;

namespace WHLTV.DemoDownload.Worker.Workers;

public sealed class DownloadWorker : BackgroundService
{
    private readonly DemoDownloadJobRepository _jobs;
    private readonly DemoPipelineLogsRepository _dbLogger;
    private readonly ProcessRunner _processRunner;
    private readonly DockerRunner _dockerRunner;
    private readonly ILogger<DownloadWorker> _logger;

    public DownloadWorker(
        DemoDownloadJobRepository jobs,
        DemoPipelineLogsRepository dbLogger,
        ProcessRunner processRunner,
        DockerRunner dockerRunner,
        ILogger<DownloadWorker> logger)
    {
        _jobs = jobs;
        _dbLogger = dbLogger;
        _processRunner = processRunner;
        _dockerRunner = dockerRunner;
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
            var logID = await _dbLogger.LogStatusStart(PipelineEntityType.DemoDownloadJob
                                                 , job.DemoDownloadJobID
                                                 , DemoDownloadStatus.Downloading.ToString()
                                                 , PipelineStageStatus.Started);

            try
            {
                var outputDirectory = Path.GetFullPath($"demo-downloads/job-{job.DemoDownloadJobID}");
                Directory.CreateDirectory(outputDirectory);
                var result = await _dockerRunner.RunAsync(
                    new DockerRunOptions
                    {
                        ImageName = "ghcr.io/willholt1/demo-downloader:1.5.0",
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

                await _dbLogger.LogStatusEnd(logID, exitCode: result.ExitCode);

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