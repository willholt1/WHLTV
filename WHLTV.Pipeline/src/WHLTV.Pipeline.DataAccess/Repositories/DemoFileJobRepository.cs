using Dapper;
using WHLTV.Pipeline.DataAccess.Connection;
using WHLTV.Pipeline.Domain.Jobs;

namespace WHLTV.Pipeline.DataAccess.Repositories;

public sealed class DemoFileJobRepository
{
    private readonly DbConnectionFactory _connectionFactory;

    public DemoFileJobRepository(DbConnectionFactory connectionFactory)
    {
        _connectionFactory = connectionFactory;
    }

    public async Task<DemoFileJob?> TryClaimPendingConvertJob()
    {
        const string sql = """
            WITH next_job AS (
                SELECT demofilejobid
                FROM dbo.tbldemofilejobs
                WHERE status = 'ReadyToConvert'
                ORDER BY createdat
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            )
            UPDATE dbo.tbldemofilejobs AS j
            SET status = 'Converting',
                startedat = now(),
                attemptcount = j.attemptcount + 1,
                updatedat = now()
            FROM next_job
            WHERE j.demofilejobid = next_job.demofilejobid
            RETURNING
                j.demofilejobid AS DemoFileJobID,
                j.demodownloadjobid AS DemoDownloadJobID,
                j.demorelativepath AS DemoRelativePath,
                j.parquettemprelativepath AS ParquetTempRelativePath,
                j.parquetfinalrelativepath AS ParquetFinalRelativePath,
                j.status AS Status,
                j.attemptcount AS AttemptCount;
            """;

        using var connection = _connectionFactory.CreateConnection();

        return await connection.QuerySingleOrDefaultAsync<DemoFileJob>(sql);
    }
}