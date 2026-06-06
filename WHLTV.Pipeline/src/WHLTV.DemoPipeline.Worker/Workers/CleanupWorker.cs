namespace WHLTV.DemoPipeline.Worker.Workers;

public sealed class CleanupWorker : BackgroundService
{
    private readonly ILogger<CleanupWorker> _logger;

    public CleanupWorker(ILogger<CleanupWorker> logger)
    {
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        _logger.LogInformation("Cleanup worker is currently a placeholder and is not configured to process jobs.");

        while (!stoppingToken.IsCancellationRequested)
        {
            await Task.Delay(TimeSpan.FromMinutes(1), stoppingToken);
        }
    }
}