using Dapper;
using WHLTV.Pipeline.DataAccess.Connection;
using WHLTV.Pipeline.Domain.Jobs;
using WHLTV.Pipeline.Domain.Enums;

namespace WHLTV.Pipeline.DataAccess.Repositories;

public sealed class DemoDownloadJobRepository
{
    private readonly DbConnectionFactory _connectionFactory;

    public DemoDownloadJobRepository(DbConnectionFactory connectionFactory)
    {
        _connectionFactory = connectionFactory;
    }

    public async Task<int> LogStatusStart(PipelineEntityType entityType, int entityId, string stageName, PipelineStageStaus status)
    {
        const string sql = """
            INSERT INTO tbldemopipelinelogs (
                entitytype
                ,entityid
                ,stagename
                ,status
            ) 
            VALUES (
                    @EntityType
                    ,@EntityId
                    ,@StageName
                    ,@Status
            )
            RETURNING pipelinestagelogid;
            """;

        using var connection = _connectionFactory.CreateConnection();

        var insertedId = await connection.QuerySingleAsync<int>(sql, new
        {
            EntityType = entityType,
            EntityId = entityId,
            StageName = stageName,
            Status = status
        });
        return insertedId;
    }

    public async Task LogStatusEnd(int demoPipelineLogId, int? exitCode = null, string? errorMessage = null)
    {
        const string sql = """
            UPDATE tbldemopipelinelogs
            SET completedat = now()
                ,exitcode = @ExitCode
                ,errormessage = @ErrorMessage
            WHERE pipelinestagelogid = @DemoPipelineLogID
            """;

        using var connection = _connectionFactory.CreateConnection();

        await connection.ExecuteAsync(sql, new
        {
            DemoPipelineLogID = demoPipelineLogId,
            ExitCode = exitCode,
            ErrorMessage = errorMessage
        });
    }

}