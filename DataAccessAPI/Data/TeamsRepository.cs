using Dapper;
using Npgsql;
using Whltv.Api.Contracts.Responses.Database;

namespace Whltv.Api.Data;

public sealed class TeamsRepository : ITeamsRepository
{
    private readonly NpgsqlDataSource _dataSource;

    public TeamsRepository(NpgsqlDataSource dataSource)
    {
        _dataSource = dataSource;
    }

    public async Task<IReadOnlyList<TeamsResponse>> GetTeamsAsync(CancellationToken cancellationToken = default)
    {
        const string sql = """
            SELECT *
            FROM udf_get_teams();
            """;

        await using var connection = await _dataSource.OpenConnectionAsync(cancellationToken);

        var results = await connection.QueryAsync<TeamsResponse>(
            new CommandDefinition(
                sql,
                cancellationToken: cancellationToken
            ));

        return results.AsList();
    }
}