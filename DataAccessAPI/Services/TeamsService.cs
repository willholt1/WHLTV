using Whltv.Api.Contracts.Responses.Database;
using Whltv.Api.Data;

namespace Whltv.Api.Services;

public sealed class TeamsService : ITeamsService
{
    private readonly ITeamsRepository _teamsRepository;

    public TeamsService(ITeamsRepository teamsRepository)
    {
        _teamsRepository = teamsRepository;
    }

    public Task<IReadOnlyList<TeamsResponse>> GetTeamsAsync(CancellationToken cancellationToken = default)
    {
        return _teamsRepository.GetTeamsAsync(cancellationToken);
    }
}