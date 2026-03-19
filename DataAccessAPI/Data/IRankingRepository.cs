using Whltv.Api.Contracts.Responses.Database;

namespace Whltv.Api.Data;

public interface IRankingRepository
{
    Task<IReadOnlyList<CurrentRankingResponse>> GetCurrentRankingsAsync(int topX = 10, bool vrsRanking = false, CancellationToken cancellationToken = default);
}