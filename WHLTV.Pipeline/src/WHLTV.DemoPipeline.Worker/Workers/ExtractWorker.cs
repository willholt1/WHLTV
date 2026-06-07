using WHLTV.Pipeline.DataAccess.Repositories;
using WHLTV.Pipeline.Infrastructure.Processes;
using WHLTV.Pipeline.Domain.Enums;
using System.Reflection.Metadata.Ecma335;

namespace WHLTV.DemoPipeline.Worker.Workers;

public sealed class ExtractWorker : BackgroundService
{
    private readonly DemoDownloadJobRepository _jobs;
    private readonly ArchiveExtractor _archiveExtractor;
    private readonly PathResolver _pathResolver;
    private readonly DemoPipelineLogsRepository _dbLogger;
    private readonly ILogger<ExtractWorker> _logger;

    public ExtractWorker(
        DemoDownloadJobRepository jobs,
        ArchiveExtractor archiveExtractor,
        PathResolver pathResolver,
        DemoPipelineLogsRepository dbLogger,
        ILogger<ExtractWorker> logger
    )
    {
        _jobs = jobs;
        _archiveExtractor = archiveExtractor;
        _pathResolver = pathResolver;
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
                _logger.LogInformation(
                    "Extracting demo for job {JobID} from archive path {ArchivePath}",
                    job.DemoDownloadJobID,
                    job.ArchiveRelativePath
                );

                string archiveFullPath = _pathResolver.GetImportPath(job.ArchiveRelativePath);
                string extractFullPath = _pathResolver.GetWorkPath($"extracted/job-{job.DemoDownloadJobID}");

                Directory.CreateDirectory(extractFullPath);

                IReadOnlyList<string> extractedDemoFullPaths = await _archiveExtractor.ExtractRarAsync(
                                                                                        archiveFullPath
                                                                                        , extractFullPath
                                                                                        , stoppingToken
                                                                                        );

                if (extractedDemoFullPaths.Count == 0)
                {
                    throw new InvalidOperationException(
                        $"No .dem files were extracted for job {job.DemoDownloadJobID}.");
                }

                foreach (var demoFullPath in extractedDemoFullPaths)
                {
                    string fileName = Path.GetFileName(demoFullPath);
                    string demoRelativePath = $"extracted/job-{job.DemoDownloadJobID}/{fileName}";

                    // TODO: add job for each extracted demo file to tblDemoFileJobs

                    _logger.LogInformation("Created demo file job for {DemoRelativePath}", demoRelativePath);

                }

                await _downloadJobs.MarkExtracted(job.DemoDownloadJobID);

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