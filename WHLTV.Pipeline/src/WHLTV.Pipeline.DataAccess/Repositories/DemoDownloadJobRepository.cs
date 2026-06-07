using Dapper;
using WHLTV.Pipeline.DataAccess.Connection;
using WHLTV.Pipeline.Domain.Jobs;

namespace WHLTV.Pipeline.DataAccess.Repositories;

public sealed class DemoDownloadJobRepository
{
    private readonly DbConnectionFactory _connectionFactory;

    public DemoDownloadJobRepository(DbConnectionFactory connectionFactory)
    {
        _connectionFactory = connectionFactory;
    }

    public async Task<DemoDownloadJob?> TryClaimPendingDownloadJob()
    {
        const string sql = """
            WITH next_job AS (
                SELECT demodownloadjobid
                FROM dbo.tbldemodownloadjobs
                WHERE status = 'PendingDownload'
                ORDER BY createdat
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            )
            UPDATE dbo.tbldemodownloadjobs AS j
            SET status = 'Downloading',
                startedat = now(),
                attemptcount = j.attemptcount + 1,
                updatedat = now()
            FROM next_job
            WHERE j.demodownloadjobid = next_job.demodownloadjobid
            RETURNING
                j.demodownloadjobid AS DemoDownloadJobID,
                j.matchid AS MatchID,
                j.demolink AS DemoLink,
                j.status AS Status,
                j.archiverelativepath AS ArchiveRelativePath,
                j.errormessage AS ErrorMessage,
                j.attemptcount AS AttemptCount;
            """;

        using var connection = _connectionFactory.CreateConnection();

        return await connection.QuerySingleOrDefaultAsync<DemoDownloadJob>(sql);
    }

    public async Task MarkReadyToExtract(int demoDownloadJobId, string archiveRelativePath)
    {
        const string sql = """
            UPDATE dbo.tbldemodownloadjobs
            SET status = 'ReadyToExtract',
                archiverelativepath = @ArchivePath,
                updatedat = now()
            WHERE demodownloadjobid = @DemoDownloadJobID;
            """;

        using var connection = _connectionFactory.CreateConnection();

        await connection.ExecuteAsync(sql, new
        {
            DemoDownloadJobID = demoDownloadJobId,
            ArchivePath = archiveRelativePath
        });
    }

    public async Task<DemoDownloadJob?> TryClaimPendingExtractJob()
    {
        const string sql = """
            WITH next_job AS (
                SELECT demodownloadjobid
                FROM dbo.tbldemodownloadjobs
                WHERE status = 'ReadyToExtract'
                ORDER BY createdat
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            )
            UPDATE dbo.tbldemodownloadjobs AS j
            SET status = 'Extracting',
                attemptcount = j.attemptcount + 1,
                updatedat = now()
            FROM next_job
            WHERE j.demodownloadjobid = next_job.demodownloadjobid
            RETURNING
                j.demodownloadjobid AS DemoDownloadJobID,
                j.matchid AS MatchID,
                j.demolink AS DemoLink,
                j.status AS Status,
                j.archiverelativepath AS ArchiveRelativePath,
                j.errormessage AS ErrorMessage,
                j.attemptcount AS AttemptCount;
            """;

        using var connection = _connectionFactory.CreateConnection();

        return await connection.QuerySingleOrDefaultAsync<DemoDownloadJob>(sql);
    }

    // TODO: method to add jobs for extracted demo files to tblDemoFileJobs

    public async Task MarkExtracted(int demoDownloadJobId)
    {
        const string sql = """
            UPDATE dbo.tbldemodownloadjobs
            SET status = 'Extracted',
                updatedat = now()
            WHERE demodownloadjobid = @DemoDownloadJobID;
            """;

        using var connection = _connectionFactory.CreateConnection();

        await connection.ExecuteAsync(sql, new
        {
            DemoDownloadJobID = demoDownloadJobId
        });
    }

    public async Task MarkCompleted(int demoDownloadJobId)
    {
        const string sql = """
            UPDATE dbo.tbldemodownloadjobs
            SET status = 'Completed',
                completedat = now(),
                updatedat = now()
            WHERE demodownloadjobid = @DemoDownloadJobID;
            """;

        using var connection = _connectionFactory.CreateConnection();

        await connection.ExecuteAsync(sql, new
        {
            DemoDownloadJobID = demoDownloadJobId
        });
    }

    public async Task MarkFailed(int demoDownloadJobId, string errorMessage)
    {
        const string sql = """
            UPDATE dbo.tbldemodownloadjobs
            SET status = 'Failed',
                errormessage = @ErrorMessage,
                updatedat = now()
            WHERE demodownloadjobid = @DemoDownloadJobID;
            """;

        using var connection = _connectionFactory.CreateConnection();

        await connection.ExecuteAsync(sql, new
        {
            DemoDownloadJobID = demoDownloadJobId,
            ErrorMessage = errorMessage
        });
    }
}