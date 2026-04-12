using Dapper;
using Npgsql;
using Whltv.Api.Contracts.Responses.Database;

namespace Whltv.Api.Data;

public sealed class TeamRepository : ITeamRepository
{
    private readonly NpgsqlDataSource _dataSource;

    public TeamRepository(NpgsqlDataSource dataSource)
    {
        _dataSource = dataSource;
    }

    public async Task<IReadOnlyList<TeamVetoDataResponse>> GetTeamVetoDataAsync(DateTime from_date, DateTime to_date, int team_id, CancellationToken cancellationToken = default)
    {
        const string sql = """
            SELECT *
            FROM dbo.udf_get_veto_data(@p_from_date::date, @p_to_date::date, @p_team_id);
            """;

        await using var connection = await _dataSource.OpenConnectionAsync(cancellationToken);

        var results = await connection.QueryAsync<TeamVetoDataResponse>(
            new CommandDefinition(
                sql,
                new { p_from_date = from_date, p_to_date = to_date, p_team_id = team_id },
                cancellationToken: cancellationToken
            ));

        return results.AsList();
    }
}