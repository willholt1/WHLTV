using Dapper;
using WHLTV.Pipeline.DataAccess.Connection;
using WHLTV.Pipeline.Domain.Jobs;

namespace WHLTV.Pipeline.DataAccess.Repositories;

public sealed class DemoConversionJobRepository
{
    private readonly DbConnectionFactory _connectionFactory;

    public DemoConversionJobRepository(DbConnectionFactory connectionFactory)
    {
        _connectionFactory = connectionFactory;
    }

    public async Task<DemoConversionJob?> TryClaimPendingConvertJob()
    {
        const string sql = """
            WITH next_job AS (
                SELECT democonversionjobid
                FROM dbo.tbldemoconversionjobs
                WHERE status = 'ReadyToConvert'
                ORDER BY createdat
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            )
            UPDATE dbo.tbldemoconversionjobs AS j
            SET status = 'Converting',
                startedat = now(),
                attemptcount = j.attemptcount + 1,
                updatedat = now()
            FROM next_job
            WHERE j.democonversionjobid = next_job.democonversionjobid
            RETURNING
                j.democonversionjobid AS DemoConversionJobID,
                j.demodownloadjobid AS DemoDownloadJobID,
                j.extractedfolderrelativepath AS ExtractedFolderRelativePath,
                j.parquettempfolderrelativepath AS ParquetTempFolderRelativePath,
                j.status AS Status,
                j.attemptcount AS AttemptCount;
            """;

        using var connection = _connectionFactory.CreateConnection();

        return await connection.QuerySingleOrDefaultAsync<DemoConversionJob>(sql);
    }

    public async Task MarkReadyToValidate(int demoConversionJobId)
    {
        const string sql = """
            UPDATE dbo.tbldemoconversionjobs
            SET status = 'ReadyToValidate',
                updatedat = now()
            WHERE democonversionjobid = @DemoConversionJobID;
            """;

        using var connection = _connectionFactory.CreateConnection();

        await connection.ExecuteAsync(sql, new
        {
            DemoConversionJobID = demoConversionJobId
        });
    }

    public async Task MarkFailed(int demoConversionJobId, string errorMessage)
    {
        const string sql = """
            UPDATE dbo.tbldemoconversionjobs
            SET status = 'Failed',
                errormessage = @ErrorMessage,
                updatedat = now()
            WHERE democonversionjobid = @DemoConversionJobID;
            """;

        using var connection = _connectionFactory.CreateConnection();

        await connection.ExecuteAsync(sql, new
        {
            DemoConversionJobID = demoConversionJobId,
            ErrorMessage = errorMessage
        });
    }
}