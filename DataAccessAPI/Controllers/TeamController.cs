using Microsoft.AspNetCore.Mvc;
using Whltv.Api.Services;

namespace Whltv.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class TeamController : ControllerBase
{
    private readonly ITeamService _teamService;

    public TeamController(ITeamService teamService)
    {
        _teamService = teamService;
    }

    [HttpGet("veto-data")]
    public async Task<IActionResult> GetVetoData([FromQuery] DateTime? from_date, [FromQuery] DateTime? to_date, [FromQuery] int team_id, CancellationToken cancellationToken)
    {
        if (team_id <= 0)
        {
            return BadRequest("team_id must be greater than 0.");
        }
        
        if (from_date == null || to_date == null)
        {
            from_date = DateTime.UtcNow.AddMonths(-3);
            to_date = DateTime.UtcNow;
        }

        var rankings = await _teamService.GetTeamVetoDataAsync(from_date.Value, to_date.Value, team_id, cancellationToken);
        return Ok(rankings);
    }
}