using Whltv.Api.Contracts.Responses.Database;
using Whltv.Api.Data;

namespace Whltv.Api.Services;

public sealed class RankingService : IRankingService
{
    private readonly IRankingRepository _rankingRepository;

    public RankingService(IRankingRepository rankingRepository)
    {
        _rankingRepository = rankingRepository;
    }

    public Task<IReadOnlyList<CurrentRankingResponse>> GetCurrentRankingsAsync(
        int topX = 10,
        bool vrsRanking = false,
        CancellationToken cancellationToken = default)
    {
        return _rankingRepository.GetCurrentRankingsAsync(topX, vrsRanking, cancellationToken);
    }
}