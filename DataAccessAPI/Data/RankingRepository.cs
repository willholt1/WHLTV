using Dapper;
using Npgsql;
using Whltv.Api.Contracts.Responses.Database;

namespace Whltv.Api.Data;

public sealed class RankingRepository : IRankingRepository
{
    private readonly NpgsqlDataSource _dataSource;

    public RankingRepository(NpgsqlDataSource dataSource)
    {
        _dataSource = dataSource;
    }

    public async Task<IReadOnlyList<CurrentRankingResponse>> GetCurrentRankingsAsync(
        int topX = 10,
        bool vrsRanking = false,
        CancellationToken cancellationToken = default)
    {
        const string sql = """
            select *
            from dbo.udf_get_current_ranking(@p_top_x, @p_vrs_ranking);
            """;

        await using var connection = await _dataSource.OpenConnectionAsync(cancellationToken);

        var results = await connection.QueryAsync<CurrentRankingResponse>(
            new CommandDefinition(
                sql,
                new { p_top_x = topX, p_vrs_ranking = vrsRanking },
                cancellationToken: cancellationToken
            ));

        return results.AsList();
    }
}