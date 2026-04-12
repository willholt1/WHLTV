using Whltv.Api.Contracts.Responses.Database;
using Whltv.Api.Data;

namespace Whltv.Api.Services;

public sealed class TeamService : ITeamService
{
    private readonly ITeamRepository _teamRepository;

    public TeamService(ITeamRepository teamRepository)
    {
        _teamRepository = teamRepository;
    }

    public Task<IReadOnlyList<TeamVetoDataResponse>> GetTeamVetoDataAsync(DateTime from_date, DateTime to_date, int team_id, CancellationToken cancellationToken = default)
    {
        return _teamRepository.GetTeamVetoDataAsync(from_date, to_date, team_id, cancellationToken);
    }
}