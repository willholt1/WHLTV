using Dapper;
using WHLTV.Pipeline.DataAccess.Connection;
using WHLTV.Pipeline.Domain.Enums;

namespace WHLTV.Pipeline.DataAccess.Repositories;

public sealed class AppConfigRepository
{
    private readonly DbConnectionFactory _connectionFactory;

    public AppConfigRepository(DbConnectionFactory connectionFactory)
    {
        _connectionFactory = connectionFactory;
    }
    public async Task<bool?> GetWorkerEnabledStatus(PipelineWorkers worker)
    {
        int workerConfigId = (int)worker;

        const string sql = """
            SELECT w.enabled AS Enabled
            FROM dbo.tblWorkerConfig AS w
            WHERE w.workerConfigId = @WorkerConfigId;
            """;

        using var connection = _connectionFactory.CreateConnection();

        return await connection.QuerySingleOrDefaultAsync<bool?>(sql, new
        {
            WorkerConfigId = workerConfigId
        });
    }
}