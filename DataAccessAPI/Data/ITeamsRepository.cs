using Whltv.Api.Contracts.Responses.Database;

namespace Whltv.Api.Data;

public interface ITeamsRepository
{
    Task<IReadOnlyList<TeamsResponse>> GetTeamsAsync(CancellationToken cancellationToken = default);
}