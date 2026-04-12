using Whltv.Api.Contracts.Responses.Database;

namespace Whltv.Api.Services;

public interface ITeamService
{
    Task<IReadOnlyList<TeamVetoDataResponse>> GetTeamVetoDataAsync(DateTime from_date, DateTime to_date, int team_id, CancellationToken cancellationToken = default);
}