using Whltv.Api.Contracts.Responses.Database;

namespace Whltv.Api.Data;

public interface ITeamRepository
{
    Task<IReadOnlyList<TeamVetoDataResponse>> GetTeamVetoDataAsync(DateTime from_date, DateTime to_date, int team_id, CancellationToken cancellationToken = default);
}