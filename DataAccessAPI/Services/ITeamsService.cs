using Whltv.Api.Contracts.Responses.Database;

namespace Whltv.Api.Services;

public interface ITeamsService
{
    Task<IReadOnlyList<TeamsResponse>> GetTeamsAsync(CancellationToken cancellationToken = default);
}