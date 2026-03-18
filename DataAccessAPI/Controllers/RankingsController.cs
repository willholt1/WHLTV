using Microsoft.AspNetCore.Mvc;

namespace MyApi.Controllers;

[ApiController]
[Route("api/[controller]")]
public class RankingsController : ControllerBase
{
    [HttpGet]
    public IActionResult GetAll()
    {
        var matches = new[]
        {
            new { Rank = 1, TeamName = "Vitality", Points = 1000},
            new { Rank = 2, TeamName = "FaZe", Points = 950 }
        };

        return Ok(matches);
    }
}