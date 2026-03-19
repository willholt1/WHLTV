namespace Whltv.Api.Contracts.Responses.Database;

public sealed class CurrentRankingResponse
{
    public DateTime ranking_date { get; set; }
    public string team_name { get; set; } = string.Empty;
    public int rank { get; set; }
    public int points { get; set; }
}