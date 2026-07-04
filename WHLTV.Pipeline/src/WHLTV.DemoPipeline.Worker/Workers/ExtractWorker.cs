using WHLTV.Pipeline.DataAccess.Repositories;
using WHLTV.Pipeline.Domain.Enums;
using WHLTV.Pipeline.Infrastructure.Archives;
using WHLTV.Pipeline.Infrastructure.Storage;

namespace WHLTV.DemoPipeline.Worker.Workers;

public sealed class ExtractWorker : BackgroundService
{
    private readonly DemoDownloadJobRepository _jobs;
    private readonly ArchiveExtractor _archiveExtractor;
    private readonly PathResolver _pathResolver;
    private readonly DemoPipelineLogsRepository _dbLogger;
    private readonly ILogger<ExtractWorker> _logger;
    private readonly AppConfigRepository _appConfigRepository;

    public ExtractWorker(
        DemoDownloadJobRepository jobs,
        ArchiveExtractor archiveExtractor,
        PathResolver pathResolver,
        DemoPipelineLogsRepository dbLogger,
        ILogger<ExtractWorker> logger,
        AppConfigRepository appConfigRepository
    )
    {
        _jobs = jobs;
        _archiveExtractor = archiveExtractor;
        _pathResolver = pathResolver;
        _dbLogger = dbLogger;
        _logger = logger;
        _appConfigRepository = appConfigRepository;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            var workerEnabled = await _appConfigRepository.GetWorkerEnabledStatus(PipelineWorkers.ExtractWorker);
            if (workerEnabled == false)
            {
                _logger.LogInformation("Extract worker is disabled.");
                await Task.Delay(TimeSpan.FromSeconds(30), stoppingToken);
                continue;
            }

            var job = await _jobs.TryClaimPendingExtractJob();

            if (job is null)
            {
                _logger.LogInformation("No pending extract jobs found.");
                await Task.Delay(TimeSpan.FromSeconds(30), stoppingToken);
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
                if (string.IsNullOrWhiteSpace(job.ArchiveRelativePath))
                {
                    throw new InvalidOperationException(
                        $"Job {job.DemoDownloadJobID} is missing ArchiveRelativePath.");
                }

                _logger.LogInformation(
                    "Extracting demo for job {JobID} from archive path {ArchivePath}",
                    job.DemoDownloadJobID,
                    job.ArchiveRelativePath
                );


                string archivePath = _pathResolver.GetImportPath(job.ArchiveRelativePath);
                string extractFullPath = _pathResolver.GetWorkPath($"extracted/job-{job.DemoDownloadJobID}");

                // ArchiveRelativePath may point to a directory containing the downloaded archive(s).
                if (Directory.Exists(archivePath))
                {
                    var archiveFiles = Directory
                        .EnumerateFiles(archivePath, "*", SearchOption.TopDirectoryOnly)
                        .Where(f =>
                        {
                            var ext = Path.GetExtension(f);
                            return ext.Equals(".rar", StringComparison.OrdinalIgnoreCase)
                                || ext.Equals(".zip", StringComparison.OrdinalIgnoreCase)
                                || ext.Equals(".7z", StringComparison.OrdinalIgnoreCase);
                        })
                        .ToList();

                    if (archiveFiles.Count == 0)
                    {
                        throw new InvalidOperationException(
                            $"No archive file found in directory {archivePath} for job {job.DemoDownloadJobID}.");
                    }

                    archivePath = archiveFiles[0];
                }

                string archiveFullPath = archivePath;
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

                string extractedFolderRelativePath = $"extracted/job-{job.DemoDownloadJobID}";
                await _jobs.CreateDemoConversionJob(job.DemoDownloadJobID, extractedFolderRelativePath);
                _logger.LogInformation("Created demo convert job for {DemoRelativePath}", extractedFolderRelativePath);

                await _jobs.MarkExtracted(job.DemoDownloadJobID);
                _logger.LogInformation(
                    "Marked job {JobID} as Extracted",
                    job.DemoDownloadJobID
                );
                await _dbLogger.LogStatusEnd(logID, exitCode: 0);

            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error extracting demo for job {JobID}", job.DemoDownloadJobID);
                await _dbLogger.LogStatusEnd(logID, exitCode: 1, errorMessage: ex.Message);
                await _jobs.MarkFailed(job.DemoDownloadJobID, ex.Message);
                continue;
            }

        }

    }
}