using Microsoft.AspNetCore.Mvc;
using Whltv.Api.Services;

namespace Whltv.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class RankingsController : ControllerBase
{
    private readonly IRankingService _rankingService;

    public RankingsController(IRankingService rankingService)
    {
        _rankingService = rankingService;
    }

    [HttpGet("current")]
    public async Task<IActionResult> GetCurrent([FromQuery] int topX, bool vrsRanking, CancellationToken cancellationToken)
    {
        if (topX <= 0)
        {
            return BadRequest("topX must be greater than 0.");
        }

        var rankings = await _rankingService.GetCurrentRankingsAsync(topX, vrsRanking, cancellationToken);
        return Ok(rankings);
    }
}