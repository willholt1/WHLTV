using Whltv.Api.Contracts.Responses.Database;

namespace Whltv.Api.Services;

public interface IRankingService
{
    Task<IReadOnlyList<CurrentRankingResponse>> GetCurrentRankingsAsync(int topX = 10, bool vrsRanking = false, CancellationToken cancellationToken = default);
}