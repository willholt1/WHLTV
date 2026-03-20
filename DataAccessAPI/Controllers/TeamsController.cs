using Microsoft.AspNetCore.Mvc;
using Whltv.Api.Services;

namespace Whltv.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class TeamsController : ControllerBase
{
    private readonly ITeamsService _teamsService;

    public TeamsController(ITeamsService teamsService)
    {
        _teamsService = teamsService;
    }

    [HttpGet]
    public async Task<IActionResult> GetTeams(CancellationToken cancellationToken)
    {
        var teams = await _teamsService.GetTeamsAsync(cancellationToken);
        return Ok(teams);
    }
}