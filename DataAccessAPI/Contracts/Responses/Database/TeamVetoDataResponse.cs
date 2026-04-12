namespace Whltv.Api.Contracts.Responses.Database;

public sealed class TeamVetoDataResponse
{
    public string map_name { get; set; } = string.Empty;
    public int pick_total { get; set; }
    public int ban_total { get; set; }
    public int remaining_total { get; set; }
    public int round_dif { get; set; }
    public int ct_round_dif { get; set; }
    public int t_round_dif { get; set; }
    public int wins { get; set; }
    public int times_played { get; set; }
    public decimal win_pct { get; set; }
}